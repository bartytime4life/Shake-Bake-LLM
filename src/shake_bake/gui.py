"""Local browser workbench; no external assets, cloud client or automatic downloads."""

import argparse
from concurrent.futures import Future
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import queue
import re
import secrets
import socket
import sys
import threading
import time
from urllib.parse import urlsplit
import webbrowser

from . import __version__
from .collector import _read
from .contracts import Refusal
from .helper import HelperSession
from .routing import eligible_profiles, pipeline_id, validate_policy
from .shared import ConnectionPublication
from .worker import local_inventory, parse_json

ASSETS = Path(__file__).resolve().parent / "web"
DEFAULT_POLICY = Path(__file__).resolve().parent / "default-policy.json"
DEMO = Path(__file__).resolve().parent / "demo"
CONTROLLER_TIMEOUT_SECONDS = 8


class Controller:
    """One persistent owner thread supervises children across short HTTP requests."""

    def __init__(self, projects, policy_path=DEFAULT_POLICY, port=11434):
        self.projects = dict(projects)
        self.policy_path = Path(policy_path)
        self.ollama_port = port
        self.disabled = False
        self.records = {}
        self.inventory_status = {"state": "not_checked", "models": []}
        self._queue = queue.Queue(maxsize=32)
        self._session = HelperSession(projects, policy_path=policy_path, port=port)
        self._thread = threading.Thread(target=self._run, daemon=True, name="shake-bake-owner")
        self._thread.start()

    def _run(self):
        try:
            while True:
                item = self._queue.get()
                if item is None:
                    break
                future, operation, payload = item
                if not future.set_running_or_notify_cancel():
                    continue
                try:
                    future.set_result(self._handle(operation, payload))
                except Exception as error:
                    future.set_exception(error)
        finally:
            self._session.close()

    def call(self, operation, payload=None):
        if not self._thread.is_alive():
            raise Refusal("workbench_closed")
        future = Future()
        try:
            self._queue.put_nowait((future, operation, payload))
        except queue.Full:
            raise Refusal("workbench_busy") from None
        try:
            return future.result(timeout=CONTROLLER_TIMEOUT_SECONDS)
        except TimeoutError:
            # A queued start/settings request must not execute after its caller
            # already received a timeout. Running operations retain their bounds.
            future.cancel()
            raise Refusal("workbench_request_timeout") from None

    def _policy(self):
        try:
            resolved = self.policy_path.resolve()
            if any(root.resolve() == resolved or root.resolve() in resolved.parents for root in self.projects.values()):
                raise Refusal("routing_policy_inside_source")
            policy = validate_policy(parse_json(_read(self.policy_path.parent, self.policy_path.name).decode()))
            profiles = []
            fingerprint = pipeline_id()
            for kind in ("code", "troubleshoot", "documents", "search"):
                eligible, rejected = eligible_profiles(policy, kind, fingerprint)
                eligible_ids = {p["id"] for p in eligible}
                reasons = dict(rejected)
                for profile in policy["profiles"]:
                    if profile["task_kind"] == kind:
                        profiles.append({"id": profile["id"], "model": profile["model"], "task_kind": kind,
                                         "status": "review_record_valid" if profile["id"] in eligible_ids else profile["status"],
                                         "reason": reasons.get(profile["id"]), "evaluation": profile["evaluation"]})
            return {"enabled": policy["enabled"], "profiles": profiles, "error": None}
        except (Refusal, OSError, UnicodeError):
            return {"enabled": False, "profiles": [], "error": "policy_unavailable"}

    def _result(self, identifier):
        result = self._session.get_result(identifier)
        result["task_kind"] = self.records.get(identifier, {}).get("task_kind", "code")
        result["entry_point"] = self.records.get(identifier, {}).get("entry_point", "workspace")
        if result["state"] == "DONE":
            result["evidence"] = [self._session.fetch_evidence(identifier, item["evidence_id"]) for item in result.get("evidence", [])]
        return result

    def _adapter(self, payload):
        method, arguments, projects = payload["method"], payload["arguments"], payload["projects"]
        if not isinstance(arguments, dict):
            raise Refusal("invalid_shared_request")
        if method == "list_projects" and not arguments:
            return {"mode": "shared_accuracy_routed", "projects": sorted(projects),
                    "local_ai_paused": self.disabled or not self._policy()["enabled"], "max_active_tasks": 1}
        if method == "start_task":
            if set(arguments) != {"project_id", "task", "task_kind"} or arguments["project_id"] not in projects:
                raise Refusal("project_not_permitted")
            return self._start(arguments, entry_point="assistant")
        expected = {"task_id", "evidence_id"} if method == "fetch_evidence" else {"task_id"}
        if method not in ("get_result", "fetch_evidence", "cancel_task") or set(arguments) != expected:
            raise Refusal("invalid_shared_request")
        identifier = arguments["task_id"]
        if not isinstance(identifier, str) or self.records.get(identifier, {}).get("project_id") not in projects:
            raise Refusal("task_not_permitted")
        if method == "fetch_evidence":
            return self._session.fetch_evidence(identifier, arguments["evidence_id"])
        if method == "cancel_task":
            return self._session.cancel_task(identifier)
        result = self._session.get_result(identifier)
        result["task_kind"] = self.records[identifier]["task_kind"]
        result["entry_point"] = self.records[identifier].get("entry_point", "workspace")
        return result

    def _start(self, payload, *, entry_point="workspace"):
        if not isinstance(payload, dict) or set(payload) != {"project_id", "task", "task_kind"}:
            raise Refusal("invalid_task_request")
        started = self._session.start_task(payload["project_id"], payload["task"], task_kind=payload["task_kind"], disabled=self.disabled)
        self.records[started["task_id"]] = {"project_id": payload["project_id"], "task_kind": payload["task_kind"],
                                           "task": payload["task"], "created": time.time(), "entry_point": entry_point}
        while len(self.records) > 8:
            del self.records[next(iter(self.records))]
        return started

    def _handle(self, operation, payload):
        if operation == "adapter":
            return self._adapter(payload)
        if operation == "state":
            recent = []
            for identifier, metadata in list(self.records.items()):
                try:
                    state = self._session.get_result(identifier)["state"]
                except Refusal:
                    state = "EXPIRED"
                recent.append({**metadata, "task_id": identifier, "state": state})
            policy = self._policy()
            return {"version": __version__, "projects": [{"id": name, "label": name.replace("-", " ").title(), "path": str(root), "demo": root == DEMO} for name, root in self.projects.items()],
                    "local_ai_enabled": not self.disabled and policy["enabled"], "policy": policy,
                    "recent": list(reversed(recent)), "inventory": self.inventory_status,
                    "catalog": json.loads((ASSETS / "models.json").read_text())}
        if operation == "start":
            return self._start(payload)
        if operation == "result":
            return self._result(payload)
        if operation == "cancel":
            return self._session.cancel_task(payload)
        if operation == "settings":
            if not isinstance(payload, dict) or set(payload) != {"enabled"} or type(payload["enabled"]) is not bool:
                raise Refusal("invalid_settings")
            self.disabled = not payload["enabled"]
            if self.disabled:
                for identifier in self.records:
                    try:
                        self._session.cancel_task(identifier)
                    except Refusal:
                        pass
            return {"enabled": not self.disabled and self._policy()["enabled"]}
        if operation == "inventory":
            try:
                inventory = local_inventory(self.ollama_port, time.monotonic()+5)
                self.inventory_status = {"state": "connected", "models": [{"name": name, "digest": digest} for name, digest in inventory.items()]}
            except Refusal:
                self.inventory_status = {"state": "unavailable", "models": []}
            return self.inventory_status
        raise Refusal("unknown_operation")

    def close(self):
        self._queue.put(None, timeout=2)
        self._thread.join(timeout=4)
        if self._thread.is_alive():
            raise RuntimeError("workbench owner did not stop")


class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 8

    def __init__(self, address, controller, *, max_connections=8, idle_seconds=3, connection_seconds=12, adapter_projects=None):
        if address[0] != "127.0.0.1":
            raise Refusal("loopback_ui_required")
        if (type(max_connections) is not int or not 1 <= max_connections <= 32 or
            any(type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= 30
                for value in (idle_seconds, connection_seconds))):
            raise Refusal("invalid_connection_limits")
        self.max_connections = max_connections
        self.idle_seconds = idle_seconds
        self.connection_seconds = connection_seconds
        self._connections = {}
        self._connections_lock = threading.Lock()
        self.controller = controller
        if adapter_projects is not None and (not isinstance(adapter_projects, (tuple, list)) or not adapter_projects or
            any(not isinstance(name, str) or name not in controller.projects for name in adapter_projects)):
            raise Refusal("invalid_adapter_projects")
        self.adapter_projects = tuple(adapter_projects or ())
        self.adapter_token = secrets.token_urlsafe(32) if adapter_projects is not None else None
        self.session_token = secrets.token_urlsafe(32)
        self.csrf_token = secrets.token_urlsafe(32)
        super().__init__(address, Handler)
        self.origins = {f"http://127.0.0.1:{self.server_port}", f"http://localhost:{self.server_port}"}
        self.hosts = {urlsplit(origin).netloc for origin in self.origins}

    def process_request(self, request, client_address):
        with self._connections_lock:
            admitted = len(self._connections) < self.max_connections
            if admitted:
                self._connections[request] = time.monotonic() + self.connection_seconds
        if not admitted:
            # Do not allocate a handler or wait on an overloaded connection.
            try:
                request.setblocking(False)
                request.send(b"HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\nRetry-After: 1\r\nCache-Control: no-store\r\n\r\n")
            except OSError:
                pass
            self.shutdown_request(request)
            return
        try:
            request.settimeout(self.idle_seconds)
            super().process_request(request, client_address)
        except Exception:
            with self._connections_lock:
                self._connections.pop(request, None)
            self.shutdown_request(request)
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            with self._connections_lock:
                self._connections.pop(request, None)

    @staticmethod
    def _disconnect(request):
        try:
            request.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def service_actions(self):
        super().service_actions()
        now = time.monotonic()
        with self._connections_lock:
            expired = [request for request, deadline in self._connections.items() if now >= deadline]
        # An absolute deadline catches header/body drips that reset idle timers.
        # Main serve_forever polls at 0.2 s; deadlines are cooperative, not realtime.
        for request in expired:
            self._disconnect(request)

    def server_close(self):
        with self._connections_lock:
            active = tuple(self._connections)
        for request in active:
            self._disconnect(request)
        super().server_close()

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (TimeoutError, ConnectionError, OSError)):
            return
        super().handle_error(request, client_address)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *args):
        pass

    def _send(self, status, content, mime="application/json; charset=utf-8", cookie=False):
        raw = content if isinstance(content, bytes) else json.dumps(content, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        if cookie:
            self.send_header("Set-Cookie", f"sb_session={self.server.session_token}; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _allowed(self, post=False):
        if self.headers.get("Host") not in self.server.hosts:
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin not in self.server.origins:
            return False
        try:
            cookie = SimpleCookie(self.headers.get("Cookie", ""))
            token = cookie.get("sb_session")
            authenticated = token and secrets.compare_digest(token.value, self.server.session_token)
        except Exception:
            authenticated = False
        if not authenticated or self.headers.get("Sec-Fetch-Site") == "cross-site":
            return False
        try:
            return not post or (origin in self.server.origins and secrets.compare_digest(self.headers.get("X-SB-CSRF", ""), self.server.csrf_token))
        except TypeError:
            return False

    def do_GET(self):
        if self.headers.get("Host") not in self.server.hosts:
            self._send(403, {"error": "host_not_allowed"}); return
        path = urlsplit(self.path).path
        static = {"/": ("index.html", "text/html; charset=utf-8"), "/styles.css": ("styles.css", "text/css; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8")}
        if path in static:
            name, mime = static[path]
            self._send(200, (ASSETS / name).read_bytes(), mime, cookie=path=="/"); return
        if not self._allowed():
            self._send(403, {"error": "session_required"}); return
        try:
            if path == "/api/state":
                state = self.server.controller.call("state")
                state["csrf_token"] = self.server.csrf_token
                self._send(200, state)
            elif re.fullmatch(r"/api/tasks/[a-f0-9]{32}", path):
                self._send(200, self.server.controller.call("result", path.rsplit("/", 1)[-1]))
            else:
                self._send(404, {"error": "not_found"})
        except Refusal as error:
            self._send(400, {"error": error.code})
        except Exception:
            self._send(503, {"error": "workbench_unavailable"})

    def do_POST(self):
        shared = urlsplit(self.path).path == "/api/helper"
        try:
            shared_allowed = (self.headers.get("Host") in self.server.hosts and self.server.adapter_token is not None and
                              self.headers.get("Origin") is None and self.headers.get("Sec-Fetch-Site") is None and
                              secrets.compare_digest(self.headers.get("Authorization", ""), "Bearer " + self.server.adapter_token))
        except TypeError:
            shared_allowed = False
        if (shared and not shared_allowed) or (not shared and not self._allowed(post=True)):
            self._send(403, {"error": "request_not_allowed"}); return
        try:
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise Refusal("json_required")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 24000:
                raise Refusal("request_size")
            self.connection.settimeout(3)
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise Refusal("request_incomplete")
            payload = parse_json(raw.decode("utf-8"))
            path = urlsplit(self.path).path
            if shared:
                if not isinstance(payload, dict) or set(payload) != {"method", "arguments"} or not isinstance(payload["method"], str):
                    raise Refusal("invalid_shared_request")
                try:
                    value = self.server.controller.call("adapter", {**payload, "projects": self.server.adapter_projects})
                except Refusal as error:
                    value = {"outcome": "DENY", "code": error.code}
                self._send(200, {"result": value})
            elif path == "/api/tasks":
                self._send(202, self.server.controller.call("start", payload))
            elif path == "/api/settings":
                self._send(200, self.server.controller.call("settings", payload))
            elif path == "/api/inventory" and payload == {}:
                self._send(200, self.server.controller.call("inventory"))
            elif re.fullmatch(r"/api/tasks/[a-f0-9]{32}/cancel", path) and payload == {}:
                self._send(200, self.server.controller.call("cancel", path.split("/")[-2]))
            else:
                self._send(404, {"error": "not_found"})
        except (Refusal, ValueError, UnicodeError) as error:
            self._send(400, {"error": error.code if isinstance(error, Refusal) else "invalid_request"})
        except Exception:
            self._send(503, {"error": "workbench_unavailable"})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", action="append", help="Approved ID=/absolute/folder; repeat up to eight")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--port", type=int, default=8421)
    parser.add_argument("--ollama-port", type=int, default=11434)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--connection-file", type=Path, help="Publish a private local adapter connection file outside inspected projects")
    parser.add_argument("--adapter-project", action="append", help="Project ID permitted to the adapter; default starter-demo only")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535 or not 1 <= args.ollama_port <= 65535:
        parser.error("--port and --ollama-port must be between 1 and 65535")
    if args.adapter_project and args.connection_file is None:
        parser.error("--adapter-project requires --connection-file")
    projects = {"starter-demo": DEMO}
    for entry in args.project or []:
        name, separator, path = entry.partition("=")
        if not separator or not Path(path).is_absolute() or name in projects:
            parser.error("use distinct ID=/absolute/folder entries")
        projects[name] = Path(path)
    try:
        controller = Controller(projects, args.policy, args.ollama_port)
    except Refusal as error:
        print("The workbench could not start: "+error.code, file=sys.stderr)
        return 2
    server, publication = None, None
    try:
        try:
            server = WorkbenchServer(("127.0.0.1", args.port), controller,
                                     adapter_projects=tuple(args.adapter_project or ["starter-demo"]) if args.connection_file else None)
        except OSError:
            print("That local port is unavailable. Try another with --port.", file=sys.stderr)
            return 2
        if args.connection_file is not None:
            publication = ConnectionPublication(args.connection_file, server.server_port, server.adapter_token, projects.values())
        url = f"http://127.0.0.1:{server.server_port}"
        print(f"Local: {url}", flush=True)
        if publication is not None:
            print("Private assistant connection file ready. Actual host integration remains unqualified.", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
    except (Refusal, OSError) as error:
        print("The shared workbench could not start: " + (error.code if isinstance(error, Refusal) else "local_startup_failed"), file=sys.stderr)
        return 2
    finally:
        try:
            if server is not None:
                server.server_close()
        finally:
            try:
                if publication is not None:
                    publication.close()
            finally:
                controller.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
