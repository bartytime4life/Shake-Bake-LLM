"""Private Unix socket for native clients sharing the GUI's actual coordinator."""

import hmac
import json
import os
from pathlib import Path
import secrets
import socket
import socketserver
import stat
import threading

from .contracts import Refusal
from .jsonutil import strict_json
from .policy import _open_directory

INPUT_LIMIT = 64 * 1024
OUTPUT_LIMIT = 512 * 1024
METHODS = {"start_job", "get_result", "fetch_evidence", "cancel_job"}


class PrivateServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    block_on_close = False

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        super().process_request(request, client_address)

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


class SharedCoordinator:
    def __init__(self, engine):
        self.engine = engine
        self.token = secrets.token_urlsafe(32)
        self.path = engine.store.directory / "connection.json"
        # A short private socket path also works when the state path approaches AF_UNIX's limit.
        self.socket_path = engine.store.directory / "native.sock"
        if len(os.fsencode(self.socket_path)) >= 100:
            raise Refusal("ipc_path", "Use a shorter private state-directory path for shared native clients.")
        if self.path.exists() or self.path.is_symlink() or self.socket_path.exists() or self.socket_path.is_symlink():
            raise Refusal("ipc_existing", "A prior private connection publication exists. Verify that service is stopped before archiving stale connection.json/native.sock files.")
        owner = self
        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                self.connection.settimeout(3)
                def expire():
                    try:
                        self.connection.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                timer = threading.Timer(5, expire)
                timer.daemon = True
                timer.start()
                try:
                    raw = self.rfile.readline(INPUT_LIMIT + 1)
                    if len(raw) > INPUT_LIMIT or not raw.endswith(b"\n"):
                        raise Refusal("ipc_size", "The native request exceeded its size/framing limit.")
                    call = strict_json(raw)
                    if not isinstance(call, dict) or set(call) != {"token", "method", "arguments"} or not isinstance(call["token"], str) or not hmac.compare_digest(call["token"], owner.token):
                        raise Refusal("ipc_auth", "The native client could not authenticate.")
                    method, arguments = call["method"], call["arguments"]
                    if not isinstance(method, str) or method not in METHODS or not isinstance(arguments, dict):
                        raise Refusal("ipc_method", "Only the four scoped job/evidence methods are exposed.")
                    result = getattr(owner.engine, method)(**arguments)
                    response = {"ok": True, "result": result}
                except Refusal as exc:
                    response = {"ok": False, "error": exc.to_dict()}
                except Exception:
                    response = {"ok": False, "error": {"code": "ipc_request", "message": "The native request could not be processed."}}
                finally:
                    timer.cancel()
                output = json.dumps(response, ensure_ascii=False).encode() + b"\n"
                if len(output) <= OUTPUT_LIMIT:
                    try:
                        self.wfile.write(output)
                    except OSError:
                        pass
        self.server = PrivateServer(str(self.socket_path), Handler)
        self.server.slots = threading.BoundedSemaphore(4)
        os.chmod(self.socket_path, 0o600)
        publication = json.dumps({"schema_version": 1, "socket": str(self.socket_path), "token": self.token,
                                  "projects": list(engine.roots)}, separators=(",", ":")).encode()
        try:
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(publication)
                handle.flush()
                os.fsync(handle.fileno())
            info = self.path.stat()
            self.identity = (info.st_dev, info.st_ino, publication)
        except Exception:
            self.server.server_close()
            self.socket_path.unlink(missing_ok=True)
            raise
        self.socket_identity = (self.socket_path.stat().st_dev, self.socket_path.stat().st_ino)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        try:
            info = self.path.lstat()
            if (info.st_dev, info.st_ino) == self.identity[:2] and not stat.S_ISLNK(info.st_mode) and self.path.read_bytes() == self.identity[2]:
                self.path.unlink()
            info = self.socket_path.lstat()
            if (info.st_dev, info.st_ino) == self.socket_identity:
                self.socket_path.unlink()
        except OSError:
            pass


class RemoteEngine:
    def __init__(self, publication):
        path = Path(publication).absolute()
        parent = _open_directory(path.parent)
        try:
            directory = os.fstat(parent)
            if directory.st_uid != os.getuid() or stat.S_IMODE(directory.st_mode) != 0o700:
                raise Refusal("ipc_permissions", "The connection publication must be in an owner-owned 0700 directory.")
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(fd, "rb") as handle:
                info = os.fstat(handle.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1:
                    raise Refusal("ipc_permissions", "The connection publication requires owner-only 0600 permissions.")
                raw = handle.read(8193)
            if len(raw) > 8192:
                raise Refusal("ipc_size", "The connection publication is too large.")
            self.connection = strict_json(raw)
            if not isinstance(self.connection, dict) or set(self.connection) != {"schema_version", "socket", "token", "projects"} or self.connection["schema_version"] != 1:
                raise Refusal("ipc_publication", "The connection publication has an unsupported schema.")
            if not isinstance(self.connection["token"], str) or not 32 <= len(self.connection["token"]) <= 100:
                raise Refusal("ipc_publication", "The connection token is invalid.")
            target = Path(self.connection["socket"])
            if target.parent != path.parent or target.name != "native.sock":
                raise Refusal("ipc_publication", "The native socket must be beside its private publication.")
            info = target.lstat()
            if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
                raise Refusal("ipc_permissions", "The native socket requires owner-only permissions.")
        finally:
            os.close(parent)

    def call(self, method, arguments):
        raw = json.dumps({"token": self.connection["token"], "method": method, "arguments": arguments}, ensure_ascii=False).encode() + b"\n"
        if len(raw) > INPUT_LIMIT:
            raise Refusal("ipc_size", "The native request exceeds its byte budget.")
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(5)
                connection.connect(self.connection["socket"])
                connection.sendall(raw)
                with connection.makefile("rb") as stream:
                    response = stream.readline(OUTPUT_LIMIT + 1)
            if len(response) > OUTPUT_LIMIT or not response.endswith(b"\n"):
                raise Refusal("ipc_size", "The native response exceeded its size/framing limit.")
            data = strict_json(response)
            if data.get("ok") is not True:
                error = data.get("error") or {}
                raise Refusal(error.get("code", "ipc_request"), error.get("message", "The native request was refused."))
            return data["result"]
        except OSError:
            raise Refusal("coordinator_unavailable", "The shared GUI coordinator is unavailable. Restart it and use its current connection publication.") from None

    def start_job(self, project_id, request, selections=None, **options):
        return self.call("start_job", {"project_id": project_id, "request": request, "selections": selections, **options})

    def get_result(self, project_id, job_id):
        return self.call("get_result", {"project_id": project_id, "job_id": job_id})

    def fetch_evidence(self, project_id, job_id, evidence_id):
        return self.call("fetch_evidence", {"project_id": project_id, "job_id": job_id, "evidence_id": evidence_id})

    def cancel_job(self, project_id, job_id):
        return self.call("cancel_job", {"project_id": project_id, "job_id": job_id})
