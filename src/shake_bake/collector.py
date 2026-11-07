"""Bounded POSIX evidence reads. Does not import providers or run source code."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat

from .contracts import Evidence, Packet, Refusal, Selection

MAX_FILE_BYTES = 256 * 1024
# Four primary windows plus up to six controlling-context windows (search.py).
MAX_FILES = 10
MAX_REQUEST_CHARS = 16_384
DENIED_PARTS = frozenset({".git", ".ssh", ".aws", ".gnupg", ".env", ".netrc", ".npmrc", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"})


def _parts(path: str) -> tuple[str, ...]:
    # Control characters (newlines, tabs, escapes) could let a filename pose as brief
    # structure or an instruction once rendered; such paths are not allowed at all.
    if not isinstance(path, str) or not path or "\\" in path or ":" in path or any(ord(ch) < 0x20 or ord(ch) == 0x7f for ch in path):
        raise Refusal("path_not_allowed")
    parsed = PurePosixPath(path)
    parts = parsed.parts
    if parsed.is_absolute() or not parts or ".." in parts:
        raise Refusal("path_not_allowed")
    if any(part in DENIED_PARTS or part.startswith(".env.") for part in parts):
        raise Refusal("path_not_allowed")
    return parts


def _read(root: Path, path: str) -> bytes:
    parts = _parts(path)
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise Refusal("unsupported_read_boundary")
    descriptors: list[int] = []
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        parent = os.open(root, directory_flags)
        descriptors.append(parent)
        for part in parts[:-1]:
            parent = os.open(part, directory_flags, dir_fd=parent)
            descriptors.append(parent)
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        descriptors.append(file_fd)
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            raise Refusal("regular_file_required")
        if before.st_size > MAX_FILE_BYTES:
            raise Refusal("file_too_large")
        chunks: list[bytes] = []
        remaining = MAX_FILE_BYTES + 1
        while remaining:
            chunk = os.read(file_fd, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(file_fd)
        if len(data) > MAX_FILE_BYTES:
            raise Refusal("file_too_large")
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise Refusal("source_changed_during_read")
        return data
    except OSError:
        raise Refusal("source_unavailable_or_not_allowed") from None
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def build_packet(root: Path, original_request: str, selections: tuple[Selection, ...]) -> Packet:
    if not isinstance(original_request, str) or not original_request.strip() or len(original_request) > MAX_REQUEST_CHARS:
        raise Refusal("invalid_request")
    if not 1 <= len(selections) <= MAX_FILES:
        raise Refusal("selection_count_not_allowed")
    records: list[Evidence] = []
    for selection in selections:
        if type(selection.start_line) is not int or type(selection.end_line) is not int:
            raise Refusal("invalid_line_range")
        data = _read(root, selection.path)
        if b"\x00" in data:
            raise Refusal("text_file_required")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            raise Refusal("utf8_required") from None
        lines = text.splitlines(keepends=True)
        if not 1 <= selection.start_line <= selection.end_line <= len(lines):
            raise Refusal("invalid_line_range")
        excerpt = "".join(lines[selection.start_line - 1:selection.end_line])
        records.append(Evidence(
            path=PurePosixPath(selection.path).as_posix(),
            start_line=selection.start_line,
            end_line=selection.end_line,
            text=excerpt,
            file_sha256=hashlib.sha256(data).hexdigest(),
            excerpt_sha256=hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
            size_bytes=len(data),
        ))
    identities = [(r.path, r.file_sha256, r.start_line, r.end_line) for r in records]
    snapshot = hashlib.sha256(json.dumps(identities, separators=(",", ":")).encode("utf-8")).hexdigest()
    return Packet(
        schema_version="0.1",
        outcome="ANSWER",
        kind="source_excerpt_packet",
        original_request=original_request,
        snapshot_scope="selected-files-only",
        snapshot_id=snapshot,
        evidence=tuple(records),
        limitations=(
            "Evidence collection only; no code-review or safety conclusion was produced.",
            "Only explicitly selected files are covered; this is not a repository-wide snapshot.",
            "No cloud-token saving or model performance has been measured.",
        ),
    )
