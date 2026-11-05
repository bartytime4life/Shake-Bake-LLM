"""Authenticated local-only workbench backed by the same routed Engine as MCP."""

import argparse
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
import json
import mimetypes
import os
from pathlib import Path
import secrets
import socket
import stat
import threading
import time
from urllib.parse import urlsplit
import webbrowser

from . import __version__
from .config import Configuration, load_config
from .contracts import Refusal
from .engine import Engine
from .ipc import SharedCoordinator
from .jsonutil import strict_json
from .ollama import OllamaSettings
from .store import private_directory

BODY_LIMIT = 64 * 1024


def prepare_demo(state_dir):
    """Own copies keep package-manager cache hard links outside inspected roots."""
    root = state_dir.parent / f"{state_dir.name}-demo-{__version__}"
    private_directory(root)
    for name in ("example.txt", "startup.py", "startup.log"):
        expected = files("shake_bake").joinpath("fixtures", name).read_bytes()
        target = root / name
        try:
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "rb") as handle:
                info = os.fstat(handle.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600 or handle.read(len(expected)+1) != expected:
                    raise Refusal("demo_changed", "The private demo copy changed. Preserve it and choose a fresh state directory to create a new demo.")
        else:
            with os.fdopen(fd, "wb") as handle:
                handle.write(expected)
                handle.flush()
                os.fsync(handle.fileno())
    return root


class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 8

    def __init__(self, engine, port=8421, shared=True):
        self.engine = engine
        self.slots = threading.BoundedSemaphore(8)
        self.connections = {}
        self.connection_lock = threading.Lock()
        self.sessions = {}
        self.session_lock = threading.Lock()
        self.boot_token = secrets.token_urlsafe(32)
        self.native = None
        super().__init__(("127.0.0.1", port), Handler)
        self.origin = f"http://127.0.0.1:{self.server_port}"
        try:
            if shared:
                self.native = SharedCoordinator(engine)
        except Exception:
            super().server_close()
            raise

    @property
    def launch_url(self):
        return self.origin + "/#" + self.boot_token

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            try:
                request.settimeout(0.1)
                request.sendall(b"HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            except OSError:
                pass
            request.close()
            return
        request.settimeout(3)
        with self.connection_lock:
            self.connections[request] = time.monotonic() + 12
        try:
            super().process_request(request, client_address)
        except Exception:
            with self.connection_lock:
                self.connections.pop(request, None)
            self.slots.release()
            request.close()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            with self.connection_lock:
                self.connections.pop(request, None)
            self.slots.release()

    def service_actions(self):
        with self.connection_lock:
            stale = [connection for connection, deadline in self.connections.items() if time.monotonic() >= deadline]
        for connection in stale:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def handle_error(self, *_):
        # Never log request bodies, cookies, tokens or inspected source.
        pass

    def server_close(self):
        with self.connection_lock:
            connections = list(self.connections)
        for connection in connections:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        if self.native is not None:
            self.native.close()
            self.native = None
        super().server_close()


class Handler(BaseHTTPRequestHandler):
    server_version = "ShakeBake"

    def log_message(self, *_):
        pass

    def respond(self, status, data, content_type="application/json", cookie=None):
        body = json.dumps(data, ensure_ascii=False).encode() if content_type == "application/json" else data
        self.send_response(status)
        self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith("text/") or content_type == "application/json" else ""))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.send_header("Connection", "close")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def guard_origin(self, mutation=False, public=False):
        if self.headers.get_all("Host", []) != [self.server.origin.removeprefix("http://")]:
            raise Refusal("origin", "Open the exact loopback address printed by the launcher.")
        origins = self.headers.get_all("Origin", [])
        if len(origins) > 1 or (mutation and origins != [self.server.origin]) or (origins and origins != [self.server.origin]):
            raise Refusal("origin", "This operation requires the local workbench's own origin.")
        if not public and self.headers.get("Sec-Fetch-Site") not in (None, "same-origin", "none"):
            raise Refusal("origin", "Cross-site workbench access is refused.")

    def authorize(self, mutation=False):
        self.guard_origin(mutation)
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            raise Refusal("session", "Reopen the private launch link to sign in to this local session.") from None
        sid = cookie.get("shake_session")
        with self.server.session_lock:
            csrf = self.server.sessions.get(sid.value if sid else "")
        if csrf is None:
            raise Refusal("session", "Reopen the private launch link to sign in to this local session.")
        if mutation and not secrets.compare_digest(self.headers.get("X-Shake-CSRF", ""), csrf):
            raise Refusal("csrf", "Refresh the workbench to restore its session authorization.")
        return csrf

    def body(self):
        if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) != 1:
            raise Refusal("request_framing", "Use one bounded Content-Length request.")
        if self.headers.get("Content-Type", "").split(";", 1)[0] != "application/json":
            raise Refusal("request_type", "Use a JSON request.")
        try:
            length = int(self.headers["Content-Length"])
        except ValueError:
            raise Refusal("request_size", "The request length is invalid.") from None
        if not 1 <= length <= BODY_LIMIT:
            raise Refusal("request_size", "The request exceeds the workbench's byte budget.")
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise Refusal("request_size", "The request body is incomplete.")
        value = strict_json(raw)
        if not isinstance(value, dict):
            raise Refusal("request_shape", "The request must be a JSON object.")
        return value

    def do_GET(self):
        try:
            parsed = urlsplit(self.path)
            self.guard_origin(public=not parsed.path.startswith("/api/"))
            if parsed.query or parsed.fragment:
                raise Refusal("route", "Unsupported route parameters.")
            path = parsed.path
            if path == "/api/state":
                csrf = self.authorize()
                engine = self.server.engine
                with engine._admission:
                    active = None if engine._active is None else {"job_id": engine._active[0], "project_id": engine._active[1]}
                return self.respond(200, {"version": __version__, "csrf": csrf, "projects": list(engine.roots),
                    "preferences": engine.preferences(), "recent": engine.recent_jobs(), "active": active,
                    "local_ai_allowed": engine.config.ollama.enabled, "local_ai_paused": engine._ai_paused.is_set(),
                    "device_id": engine.device_id, "pipeline_sha256": engine.pipeline,
                    "shared_native": self.server.native is not None})
            if path.startswith("/api/"):
                self.authorize()
                raise Refusal("route", "Unknown workbench route.")
            assets = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}
            icon_names = {"folder", "clock", "document", "copy", "download", "chevron-down", "map-pin", "x-mark"}
            asset = assets.get(path)
            if path.startswith("/icons/") and path.removeprefix("/icons/").removesuffix(".svg") in icon_names and path.endswith(".svg"):
                asset = path.removeprefix("/")
            if asset is None:
                return self.respond(404, {"error": {"code": "route", "message": "Page not found."}})
            content_type = mimetypes.guess_type(asset)[0] or "application/octet-stream"
            if asset.endswith(".js"):
                content_type = "text/javascript"
            return self.respond(200, files("shake_bake").joinpath("web", asset).read_bytes(), content_type)
        except Refusal as exc:
            self.respond(403, {"error": exc.to_dict()})
        except OSError:
            return

    def do_POST(self):
        try:
            self.guard_origin(mutation=True)
            if self.path == "/api/session":
                value = self.body()
                token = value.get("token")
                if set(value) != {"token"} or not isinstance(token, str) or not secrets.compare_digest(token, self.server.boot_token):
                    raise Refusal("session", "The private launch link is invalid for this service session.")
                with self.server.session_lock:
                    if len(self.server.sessions) >= 8:
                        raise Refusal("session_limit", "Close this service and relaunch to replace its local sessions.")
                    sid, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
                    self.server.sessions[sid] = csrf
                return self.respond(200, {"csrf": csrf}, cookie=f"shake_session={sid}; HttpOnly; SameSite=Strict; Path=/")
            self.authorize(mutation=True)
            value = self.body()
            engine = self.server.engine
            if self.path == "/api/start":
                allowed = {"project_id", "request", "selections", "task_kind", "ai_mode", "model", "digest"}
                if set(value) - allowed or not {"project_id", "request"} <= set(value):
                    raise Refusal("request_shape", "The task has unsupported fields.")
                return self.respond(200, engine.start_job(**value))
            if self.path == "/api/result":
                if set(value) != {"project_id", "job_id"}:
                    raise Refusal("request_shape", "A result requires project_id and job_id.")
                return self.respond(200, engine.get_result(**value))
            if self.path == "/api/cancel":
                if set(value) != {"project_id", "job_id"}:
                    raise Refusal("request_shape", "Cancellation requires project_id and job_id.")
                return self.respond(200, engine.cancel_job(**value))
            if self.path == "/api/preferences":
                return self.respond(200, engine.save_preferences(value))
            if self.path == "/api/pause":
                if set(value) != {"paused"}:
                    raise Refusal("request_shape", "Pause requires one boolean paused value.")
                return self.respond(200, engine.pause_local_ai(value["paused"]))
            if self.path == "/api/models":
                if value:
                    raise Refusal("request_shape", "Model refresh accepts no configuration changes.")
                return self.respond(200, engine.inventory())
            raise Refusal("route", "Unknown workbench route.")
        except Refusal as exc:
            self.respond(409 if exc.code == "busy" else 400, {"error": exc.to_dict()})
        except (OSError, TimeoutError):
            return
        except Exception:
            self.respond(400, {"error": {"code": "request_invalid", "message": "The local request could not be processed."}})


def main(argv=None):
    parser = argparse.ArgumentParser(description="Open the standalone local Shake & Bake workbench.")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--state-dir", type=Path, default=Path.home() / ".local/state/shake-bake")
    parser.add_argument("--port", type=int, default=8421)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--enable-local-ai", action="store_true", help="Allow explicit local Ollama inventory/trials for the bundled demo. Real project permissions remain in --config.")
    args = parser.parse_args(argv)
    if args.config and args.enable_local_ai:
        parser.error("Set ollama.enabled in your owner-controlled configuration when using --config.")
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    try:
        state_dir = args.state_dir.absolute()
        config = load_config(args.config) if args.config else Configuration(state_dir,
            {"demo": prepare_demo(state_dir)}, OllamaSettings(enabled=args.enable_local_ai))
        with Engine(config) as engine:
            server = WorkbenchServer(engine, args.port)
            print(server.launch_url, flush=True)
            print("Local session only. Source and model notes stay separate. Stop with Ctrl+C.", flush=True)
            if not args.no_browser:
                webbrowser.open(server.launch_url)
            try:
                server.serve_forever(poll_interval=0.1)
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
        return 0
    except Refusal as exc:
        print(json.dumps({"status": "refused", "error": exc.to_dict()}))
        return 2
    except OSError:
        print('{"status":"failed","error":{"code":"gui_startup","message":"The local workbench could not start. Check port availability, the private state path and permissions."}}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
