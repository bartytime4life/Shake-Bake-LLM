"""POSIX descriptor-relative reads. Source text cannot expand these permissions."""

from contextlib import contextmanager
from hashlib import sha256
import os
from pathlib import Path
import re
import stat
import time

from .contracts import MAX_EXCERPT_BYTES, MAX_FILE_BYTES, Evidence, Refusal, Selection

_DENIED_NAMES = {"credentials", "credentials.json", "secrets.json", "secrets.yaml", "secrets.yml", "id_rsa", "id_ed25519"}
_DENIED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keystore"}
_SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:[A-Z ]*PRIVATE KEY|OPENSSH PRIVATE KEY)-----"),
    re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,})\b"),
    re.compile(rb"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*['\"]?[^\s'\"<>]{12,}"),
    re.compile(rb"(?i)authorization\s*[:=]\s*['\"]?(?:bearer|basic)\s+[^\s'\"]{12,}"),
)


def require_posix():
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise Refusal("unsupported_platform", "This collector requires POSIX no-follow descriptor-relative reads.")


def _open_directory(path: Path) -> int:
    """Open every component from / without following symlinks, including ancestors."""
    require_posix()
    if not path.is_absolute() or ".." in path.parts:
        raise Refusal("invalid_root", "The configured root must be an absolute directory without parent traversal.")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
        return fd
    except OSError:
        os.close(fd)
        raise Refusal("root_unavailable", "The approved root is unavailable or contains a symlink.") from None


def path_parts(path: str) -> tuple[str, ...]:
    # Use only the portable '/' form. Do not normalize traversal into an allowed path.
    if "\\" in path or path.startswith("/") or any(ord(c) < 32 or ord(c) == 127 for c in path):
        raise Refusal("path_denied", "Use a relative path with / separators and no control characters.")
    parts = tuple(path.split("/"))
    if any(not p or p in {".", ".."} or p.startswith(".") for p in parts):
        raise Refusal("path_denied", "Hidden paths, traversal and empty path components are excluded.")
    if any(p.lower() in _DENIED_NAMES or Path(p).suffix.lower() in _DENIED_SUFFIXES for p in parts):
        raise Refusal("credential_path", "Credential and private-key paths are excluded.")
    return parts


def check_cancel(cancel, deadline: float):
    if cancel.is_set():
        raise Refusal("cancelled", "Collection was cancelled.")
    if time.monotonic() >= deadline:
        raise Refusal("deadline", "Collection exceeded its time budget.")


class ProjectRoot:
    def __init__(self, root: Path):
        self.path = Path(os.path.abspath(root))
        self.fd = _open_directory(self.path)
        identity = os.fstat(self.fd)
        self.identity = (identity.st_dev, identity.st_ino)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def _check_root(self):
        fresh_fd = _open_directory(self.path)
        try:
            current = os.fstat(fresh_fd)
            if (current.st_dev, current.st_ino) != self.identity:
                raise Refusal("root_changed", "The approved root changed; restart with the intended project.")
        finally:
            os.close(fresh_fd)

    @contextmanager
    def _open_file(self, parts):
        parent = os.dup(self.fd)
        file_fd = None
        try:
            for part in parts[:-1]:
                nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                os.close(parent)
                parent = nxt
            file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            yield file_fd
        except OSError:
            raise Refusal("file_unavailable", "The selected file is unavailable or contains a symlink.") from None
        finally:
            if file_fd is not None:
                os.close(file_fd)
            os.close(parent)

    def read_source(self, path: str, cancel, deadline: float) -> bytes:
        check_cancel(cancel, deadline)
        parts = path_parts(path)
        # Refuse a moved/replaced root; an open descriptor alone could retain stale access.
        self._check_root()
        with self._open_file(parts) as fd:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise Refusal("file_type_denied", "Only regular files with one hard link may be collected.")
            if before.st_size > MAX_FILE_BYTES:
                raise Refusal("file_too_large", f"The file exceeds {MAX_FILE_BYTES} bytes.")
            chunks = []
            total = 0
            while True:
                check_cancel(cancel, deadline)
                chunk = os.read(fd, min(16384, MAX_FILE_BYTES + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_FILE_BYTES:
                    raise Refusal("file_too_large", f"The file exceeds {MAX_FILE_BYTES} bytes.")
            after = os.fstat(fd)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
        if any(getattr(before, x) != getattr(after, x) for x in fields) or total != before.st_size:
            raise Refusal("source_changed", "The source changed while it was read; collect a new snapshot.")
        # A path replacement can leave the original open descriptor unchanged.
        # Reopen the current path and compare before making any captured bytes visible.
        self._check_root()
        with self._open_file(parts) as current_fd:
            current = os.fstat(current_fd)
        if any(getattr(after, x) != getattr(current, x) for x in fields):
            raise Refusal("source_changed", "The selected path changed during capture; collect a new snapshot.")
        raw = b"".join(chunks)
        if b"\0" in raw:
            raise Refusal("binary_file", "Binary files are excluded.")
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            raise Refusal("encoding", "The selected file must be valid UTF-8.") from None
        # Screen the whole bounded file, including secrets outside the selected excerpt.
        if any(pattern.search(raw) for pattern in _SECRET_PATTERNS):
            raise Refusal("possible_secret", "The file matched a credential screen. Use a sanitized source copy.")
        return raw

    def collect(self, selection: Selection, cancel, deadline: float) -> Evidence:
        raw = self.read_source(selection.path, cancel, deadline)
        # Lines are delimited by LF, with CRLF preserved byte-for-byte.
        lines = raw.split(b"\n")
        if raw.endswith(b"\n"):
            lines.pop()
        if not raw:
            lines = []
        if selection.end_line > len(lines):
            raise Refusal("range_outside_file", "The requested line range extends beyond the file.")
        selected = lines[selection.start_line - 1:selection.end_line]
        excerpt = b"\n".join(selected)
        if selection.end_line < len(lines) or raw.endswith(b"\n"):
            excerpt += b"\n"
        if len(excerpt) > MAX_EXCERPT_BYTES:
            raise Refusal("excerpt_too_large", f"The excerpt exceeds {MAX_EXCERPT_BYTES} bytes.")
        digest = sha256(raw).hexdigest()
        excerpt_digest = sha256(excerpt).hexdigest()
        identity = f"v1\0{selection.path}\0{selection.start_line}\0{selection.end_line}\0{digest}\0{excerpt_digest}"
        check_cancel(cancel, deadline)
        return Evidence(sha256(identity.encode()).hexdigest(), selection.path, selection.start_line,
                        selection.end_line, digest, excerpt_digest, len(raw), len(excerpt), excerpt.decode("utf-8"))
