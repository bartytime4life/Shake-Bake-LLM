"""Private local-service connection files and the bounded adapter client.

This is an internal loopback RPC client, not an MCP HTTP implementation.
The separate official-SDK adapter exposes MCP over stdio.
"""

import json
import os
from pathlib import Path
import re
import stat
import time

from .contracts import Refusal
from .collector import validate_request
from .task_protocol import MAX_SHARED_RESPONSE_BYTES, MAX_TASK_INPUT_BYTES
from .worker import _request, parse_json


def _private_parent(path: Path):
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise Refusal("private_connection_file_requires_posix")
    if not path.is_absolute() or not path.name or path.name in (".", ".."):
        raise Refusal("absolute_connection_file_required")
    parent = path.parent.resolve(strict=True)
    descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    info = os.fstat(descriptor)
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        os.close(descriptor)
        raise Refusal("connection_directory_must_be_private_0700")
    return descriptor


def _read_file(descriptor, name):
    file = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
    try:
        info = os.fstat(file)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
            stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > 4096):
            raise Refusal("connection_file_must_be_private_0600")
        raw = os.read(file, 4097)
        if len(raw) > 4096:
            raise Refusal("connection_file_too_large")
        return raw, info
    finally:
        os.close(file)


class ConnectionPublication:
    """Create a new private file and remove only that exact publication."""

    def __init__(self, path, port, token, source_roots):
        self.path = Path(path).expanduser().absolute()
        resolved = self.path.parent.resolve() / self.path.name
        for root in source_roots:
            root = Path(root).resolve()
            if resolved == root or root in resolved.parents:
                raise Refusal("connection_file_inside_source")
        self._descriptor = None
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = _private_parent(self.path)
        file, created_identity = None, None
        try:
            file = os.open(self.path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                           0o600, dir_fd=descriptor)
            created = os.fstat(file)
            created_identity = (created.st_dev, created.st_ino)
            os.fchmod(file, 0o600)
            self._raw = json.dumps({"schema_version": "1", "host": "127.0.0.1", "port": port, "token": token}).encode()
            with os.fdopen(file, "wb") as stream:
                file = None
                stream.write(self._raw); stream.flush(); os.fsync(stream.fileno())
                info = os.fstat(stream.fileno())
            self._identity = (info.st_dev, info.st_ino)
            self._descriptor = descriptor
        except Exception:
            if file is not None:
                os.close(file)
            if created_identity is not None:
                try:
                    current = os.stat(self.path.name, dir_fd=descriptor, follow_symlinks=False)
                    if (current.st_dev, current.st_ino) == created_identity:
                        os.unlink(self.path.name, dir_fd=descriptor)
                except OSError:
                    pass
            os.close(descriptor)
            raise Refusal("connection_file_unavailable_or_exists") from None

    def close(self):
        if self._descriptor is None:
            return
        descriptor, self._descriptor = self._descriptor, None
        try:
            try:
                raw, info = _read_file(descriptor, self.path.name)
                if (info.st_dev, info.st_ino) == self._identity and raw == self._raw:
                    os.unlink(self.path.name, dir_fd=descriptor)
            except (OSError, Refusal):
                pass
        finally:
            os.close(descriptor)


def load_connection(path):
    descriptor = None
    try:
        path = Path(path).expanduser().absolute()
        descriptor = _private_parent(path)
        raw, _ = _read_file(descriptor, path.name)
        value = parse_json(raw.decode("utf-8"))
        if (not isinstance(value, dict) or set(value) != {"schema_version", "host", "port", "token"} or
            value["schema_version"] != "1" or value["host"] != "127.0.0.1" or
            type(value["port"]) is not int or not 1 <= value["port"] <= 65535 or
            not isinstance(value["token"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{43,128}", value["token"])):
            raise Refusal("invalid_connection_file")
        return value
    except (OSError, UnicodeError, RuntimeError):
        raise Refusal("connection_file_unavailable") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)


class SharedClient:
    """One adapter client; jobs and settings stay owned by the shared service."""

    def __init__(self, connection_file):
        self._connection = load_connection(connection_file)
        self._closed = False

    def _call(self, method, arguments):
        if self._closed:
            raise Refusal("shared_client_closed")
        payload = {"method": method, "arguments": arguments}
        if len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()) > MAX_TASK_INPUT_BYTES:
            raise Refusal("shared_request_too_large")
        try:
            response = _request("POST", "/api/helper", payload, self._connection["port"],
                                time.monotonic() + 10,
                                authorization="Bearer " + self._connection["token"],
                                response_limit=MAX_SHARED_RESPONSE_BYTES, request_limit=MAX_TASK_INPUT_BYTES)
        except Refusal:
            raise Refusal("shared_service_unavailable_or_request_refused") from None
        if set(response) != {"result"} or not isinstance(response["result"], dict):
            raise Refusal("invalid_shared_response")
        return response["result"]

    def list_projects(self):
        return self._call("list_projects", {})

    def start_task(self, project_id, task, *, task_kind="code"):
        validate_request(task)
        return self._call("start_task", {"project_id": project_id, "task": task, "task_kind": task_kind})

    def get_result(self, task_id):
        return self._call("get_result", {"task_id": task_id})

    def fetch_evidence(self, task_id, evidence_id):
        return self._call("fetch_evidence", {"task_id": task_id, "evidence_id": evidence_id})

    def cancel_task(self, task_id):
        return self._call("cancel_task", {"task_id": task_id})

    def close(self):
        # Do not terminate the service or other clients' jobs. The GUI can still
        # observe/cancel retained work, which keeps its existing task deadline.
        self._closed = True
        self._connection = None
