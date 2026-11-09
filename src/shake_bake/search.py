"""Deterministic, bounded lexical selection over a trusted local checkout."""

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import re
import time

from .collector import MAX_FILES, _parts, _read, build_packet, validate_request
from .contracts import Packet, Refusal, Selection

EXTENSIONS = frozenset({".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".md", ".toml", ".yaml", ".yml", ".json", ".txt", ".c", ".h", ".cpp", ".java", ".sh", ".sql"})
EXCLUDED_DIRS = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", "vendor", "target", ".idea", ".vscode"})
STOP_WORDS = frozenset("the and for this that with from into about find show code where how does what review please have source function files file inspect controlling check".split())


@dataclass(frozen=True)
class SearchLimits:
    max_files: int = 200
    max_entries: int = 4000
    max_depth: int = 8
    seconds: float = 5.0
    excerpt_bytes: int = 16_384

    def validate(self) -> None:
        for name, ceiling in (("max_files", 1000), ("max_entries", 10000), ("max_depth", 16), ("excerpt_bytes", 65536)):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= ceiling:
                raise Refusal("invalid_search_limits")
        if type(self.seconds) not in (int, float) or not 0 < self.seconds <= 30:
            raise Refusal("invalid_search_limits")


@dataclass(frozen=True)
class SearchResult:
    original_request: str
    packet: Packet | None
    terms: tuple[str, ...]
    files_examined: int
    entries_seen: int
    source_bytes_read: int
    matching_files: int
    selected_excerpt_bytes: int
    exclusions: dict[str, int]
    cutoffs: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def prepare(root: Path, request: str, limits: SearchLimits | None = None) -> SearchResult:
    limits = limits or SearchLimits()
    limits.validate()
    validate_request(request)
    all_terms = tuple(dict.fromkeys(t.casefold() for t in re.findall(r"[A-Za-z_][A-Za-z_0-9]+", request)
                                    if len(t) >= 3 and t.casefold() not in STOP_WORDS))
    terms = all_terms[:16]
    if not terms:
        raise Refusal("search_terms_required")
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise Refusal("unsupported_read_boundary")
    deadline = time.monotonic() + limits.seconds
    excluded: dict[str, int] = {}
    cutoffs: set[str] = set()
    if len(all_terms) > len(terms):
        cutoffs.add("query_term_budget")
    candidates: list[tuple[int, str, int, int, str, int, int]] = []
    examined = entries_seen = bytes_read = 0

    def skip(reason: str) -> None:
        excluded[reason] = excluded.get(reason, 0) + 1

    def stopped() -> bool:
        if time.monotonic() >= deadline:
            cutoffs.add("time_budget")
        if examined >= limits.max_files:
            cutoffs.add("file_budget")
        return bool(cutoffs & {"time_budget", "file_budget"})

    def walk(fd: int, prefix: str, depth: int) -> None:
        nonlocal examined, entries_seen, bytes_read
        if stopped():
            return
        entries = []
        with os.scandir(fd) as iterator:
            for entry in iterator:
                if stopped():
                    return
                if entries_seen >= limits.max_entries:
                    cutoffs.add("entry_budget")
                    break
                entries_seen += 1
                entries.append(entry)
        for entry in sorted(entries, key=lambda e: e.name):
            if stopped():
                return
            path = prefix + entry.name
            try:
                _parts(path)
                if entry.is_symlink():
                    skip("symlink")
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if entry.name in EXCLUDED_DIRS:
                        skip("excluded_directory")
                        continue
                    if depth >= limits.max_depth:
                        cutoffs.add("depth_budget")
                        continue
                    if entries_seen >= limits.max_entries:
                        cutoffs.add("entry_budget")
                        continue
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    try:
                        walk(child, path + "/", depth + 1)
                    finally:
                        os.close(child)
                    continue
                if Path(entry.name).suffix.casefold() not in EXTENSIONS:
                    skip("unsupported_extension")
                    continue
                examined += 1
                data = _read(root, path)
                bytes_read += len(data)
                if b"\x00" in data:
                    skip("binary")
                    continue
                lines = data.decode("utf-8").splitlines(keepends=True)
                matches = []
                for index, line in enumerate(lines):
                    count = sum(term in line.casefold() for term in terms)
                    if count:
                        matches.append((count, index))
                path_score = sum(term in path.casefold() for term in terms)
                if not matches and not path_score:
                    continue
                score = 2 * path_score + sum(item[0] for item in matches)
                if lines:
                    # Preserve distinct nearby evidence, including a distant branch in
                    # the same file. Never replace source with a generated summary.
                    windows = []
                    for _, best in sorted(matches or [(0, 0)], key=lambda item: (-item[0], item[1])):
                        if any(begin <= best < end for begin, end in windows):
                            continue
                        windows.append((max(0, best - 3), min(len(lines), best + 4)))
                        if len(windows) == 2:
                            break
                    if any(not any(begin <= index < end for begin, end in windows) for _, index in matches):
                        cutoffs.add("window_budget")
                    digest = hashlib.sha256(data).hexdigest()
                    for rank, (begin, end) in enumerate(windows):
                        size = len("".join(lines[begin:end]).encode("utf-8"))
                        candidates.append((score, path, begin + 1, end, digest, size, rank))
            except UnicodeDecodeError:
                skip("non_utf8")
            except Refusal as refusal:
                skip(refusal.code)
            except OSError:
                skip("source_unavailable_or_not_allowed")

    try:
        root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            walk(root_fd, "", 0)
        finally:
            os.close(root_fd)
    except OSError:
        raise Refusal("source_unavailable_or_not_allowed") from None
    selected = []
    total = 0
    # Prefer one window from each file before additional windows from a file.
    for candidate in sorted(candidates, key=lambda item: (item[6], -item[0], item[1], item[2])):
        if len(selected) >= MAX_FILES:
            cutoffs.add("selection_budget")
            break
        if total + candidate[5] > limits.excerpt_bytes:
            cutoffs.add("excerpt_budget")
            continue
        selected.append(candidate)
        total += candidate[5]
    packet = None
    if selected:
        packet = build_packet(root, request, tuple(Selection(c[1], c[2], c[3]) for c in selected))
        if any(record.file_sha256 != candidate[4] for record, candidate in zip(packet.evidence, selected)):
            raise Refusal("source_changed_after_search")
    return SearchResult(request, packet, terms, examined, entries_seen, bytes_read, len({c[1] for c in candidates}), total,
                        dict(sorted(excluded.items())), tuple(sorted(cutoffs)))
