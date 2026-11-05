"""Bounded lexical windows; exact evidence is collected and rechecked separately."""

from collections import Counter
from hashlib import sha256
import os
from pathlib import Path
import re
import time

from .contracts import Refusal, Selection
from .policy import check_cancel, path_parts

SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".txt", ".log", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".rs", ".go", ".java", ".c", ".cpp", ".h", ".sh", ".sql", ".css", ".html", ".rst"}
STOP = {"the", "and", "for", "this", "that", "with", "from", "what", "why", "how", "please", "prepare", "evidence", "assistant", "investigate", "find", "source", "into", "about", "does", "which", "have", "when", "should", "could", "would", "help"}


def discover(root, request, cancel):
    deadline = time.monotonic() + 5
    terms = list(dict.fromkeys(x.lower() for x in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", request) if x.lower() not in STOP))[:32]
    stats = {"method": "bounded_lexical", "entries_seen": 0, "files_read": 0, "cutoffs": [], "refusals": {}, "exhaustive": False}
    refused = Counter()
    candidates = []
    def walk(fd, prefix, depth):
        if depth > 8:
            stats["cutoffs"].append("directory_depth")
            return
        entries = []
        with os.scandir(fd) as iterator:
            for entry in iterator:
                check_cancel(cancel, deadline)
                stats["entries_seen"] += 1
                if stats["entries_seen"] > 4000:
                    stats["cutoffs"].append("directory_entries")
                    return
                entries.append(entry)
        for entry in sorted(entries, key=lambda x: x.name):
            check_cancel(cancel, deadline)
            path = prefix + entry.name
            try:
                path_parts(path)
                if entry.is_dir(follow_symlinks=False):
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    try:
                        walk(child, path + "/", depth + 1)
                    finally:
                        os.close(child)
                elif entry.is_file(follow_symlinks=False) and (Path(path).suffix.lower() in SUFFIXES or entry.name in {"README", "LICENSE"}):
                    if stats["files_read"] >= 200:
                        stats["cutoffs"].append("file_count")
                        return
                    stats["files_read"] += 1
                    raw = root.read_source(path, cancel, deadline)
                    # Only LF is a source-line delimiter, as in the exact collector.
                    lines = raw.split(b"\n")
                    if raw.endswith(b"\n"):
                        lines.pop()
                    if not raw:
                        continue
                    scored = []
                    path_score = sum(3 for term in terms if term in path.lower())
                    for index, line in enumerate(lines):
                        if index % 128 == 0:
                            check_cancel(cancel, deadline)
                        text = line.decode("utf-8").lower()
                        score = sum(1 for term in terms if term in text)
                        if score:
                            scored.append((score + path_score, index))
                    if not scored and path_score:
                        scored = [(path_score, 0)]
                    spans = []
                    for score, index in sorted(scored, key=lambda pair: (-pair[0], pair[1])):
                        start, end = max(0, index - 5), min(len(lines), index + 10)
                        if any(start < old_end and end > old_start for old_start, old_end in spans):
                            continue
                        if len(spans) >= 2:
                            stats["cutoffs"].append("matching_windows")
                            break
                        size = len(b"\n".join(lines[start:end])) + 1
                        if size > 4096:
                            stats["cutoffs"].append("window_bytes")
                            continue
                        spans.append((start, end))
                        candidates.append((score, path, start + 1, end, sha256(raw).hexdigest(), size))
            except Refusal as exc:
                if exc.code in {"cancelled", "deadline"}:
                    raise
                refused[exc.code] += 1
            except OSError:
                refused["file_unavailable"] += 1
    try:
        walk(root.fd, "", 0)
    except Refusal as exc:
        if exc.code == "cancelled":
            raise
        stats["cutoffs"].append("scan_deadline")
    ordered = sorted(candidates, key=lambda item: (-item[0], item[1], item[2]))
    # Prioritize different files, then fill remaining slots with distant windows.
    chosen, paths = [], set()
    for candidate in ordered:
        if candidate[1] not in paths:
            chosen.append(candidate)
            paths.add(candidate[1])
            if len(chosen) == 4:
                break
    for candidate in ordered:
        if len(chosen) >= 4:
            break
        if candidate not in chosen:
            chosen.append(candidate)
    if len(chosen) < len(ordered):
        stats["cutoffs"].append("selected_windows")
    stats["cutoffs"] = sorted(set(stats["cutoffs"]))
    stats["refusals"] = dict(refused)
    stats["query_terms"] = terms
    return [(Selection(path, start, end), identity) for _, path, start, end, identity, _ in chosen], stats
