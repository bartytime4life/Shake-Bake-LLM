"""Development-only, deterministic evidence for one explicitly selected change.

The caller supplies the approved root, changed path and exact unified diff. This
module reads source but never invokes Git, executes inspected code or calls a model.
"""

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import re
import time

from .briefing import _quote
from .collector import MAX_REQUEST_CHARS, _parts, _read, build_packet
from .contracts import Packet, Refusal, Selection
from .search import EXCLUDED_DIRS, EXTENSIONS, SearchLimits

MAX_DIFF_BYTES = 16_384
MAX_DIFF_LINES = 512
MAX_HUNKS = 8
CHANGED_WINDOW_BYTES = 4_096
CONTEXT_BYTES = 12_288
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)$")
NOISE = frozenset("def class return self true false none if else elif for while from import as in and or not try except raise with pass payload receipt result value record data new old faster claimed preserve".split())


@dataclass(frozen=True)
class ContextCandidate:
    path: str
    start_line: int
    end_line: int
    file_sha256: str
    excerpt_bytes: int
    score: int
    roles: tuple[str, ...]


@dataclass(frozen=True)
class ChangeReviewEvidence:
    original_request: str
    changed_path: str
    exact_diff: str
    diff_sha256: str
    changed_source: Packet
    context: Packet | None
    context_roles: dict[str, tuple[str, ...]]
    source_bytes_read: int
    files_examined: int
    cutoffs: tuple[str, ...]
    exclusions: dict[str, int]
    missing_context_roles: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def _diff_path(line: str, marker: str) -> str:
    if not line.startswith(marker):
        raise Refusal("invalid_change_diff")
    value = line[len(marker):]
    prefix = "a/" if marker == "--- " else "b/"
    if not value.startswith(prefix):
        raise Refusal("unsupported_change_diff")
    path = value[len(prefix):]
    _parts(path)
    return path


def _line_content(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith(("\r", "\n")):
        return line[:-1]
    return line


def _verify_diff(path: str, diff: str, current_lines: list[str]) -> tuple[tuple[int, int], ...]:
    """Check new-side hunk text and line counts against captured current source."""
    lines = diff.splitlines()
    if not 1 <= len(lines) <= MAX_DIFF_LINES:
        raise Refusal("invalid_change_diff")
    first_hunk = next((i for i, line in enumerate(lines) if line.startswith("@@ ")), len(lines))
    headers = [i for i, line in enumerate(lines[:first_hunk]) if line.startswith("--- ")]
    if len(headers) != 1 or headers[0] + 1 >= len(lines):
        raise Refusal("unsupported_change_diff")
    at = headers[0]
    if _diff_path(lines[at], "--- ") != path or _diff_path(lines[at + 1], "+++ ") != path:
        raise Refusal("diff_path_mismatch")
    for line in lines[:at]:
        if line.startswith("diff --git "):
            if line != f"diff --git a/{path} b/{path}":
                raise Refusal("diff_path_mismatch")
        elif not line.startswith("index "):
            raise Refusal("unsupported_change_diff")
    if any(line.startswith(("diff --git ", "rename from ", "rename to ", "Binary files ")) for line in lines[at + 2:]):
        raise Refusal("unsupported_change_diff")
    spans: list[tuple[int, int]] = []
    index = at + 2
    previous_end = 0
    while index < len(lines):
        match = HUNK.fullmatch(lines[index])
        if match is None:
            raise Refusal("invalid_change_diff")
        try:
            old_start, old_count, new_start, new_count = (int(match[1]), int(match[2] or 1),
                                                           int(match[3]), int(match[4] or 1))
        except ValueError:
            raise Refusal("invalid_change_diff") from None
        if old_count < 0 or new_count < 0 or new_start < 1 or new_start <= previous_end:
            raise Refusal("invalid_change_diff")
        if len(spans) >= MAX_HUNKS:
            raise Refusal("change_hunk_budget")
        index += 1
        old_seen = new_seen = 0
        new_line = new_start
        changed = False
        while index < len(lines) and not lines[index].startswith("@@ "):
            line = lines[index]
            if not line or line[0] not in " +-":
                raise Refusal("unsupported_change_diff")
            if line[0] == " ":
                old_seen += 1
                new_seen += 1
            elif line[0] == "+":
                new_seen += 1
                changed = True
            else:
                old_seen += 1
                changed = True
            if line[0] != "-":
                if new_line > len(current_lines) or current_lines[new_line - 1] != line[1:]:
                    raise Refusal("diff_source_mismatch")
                new_line += 1
            if old_seen > old_count or new_seen > new_count:
                raise Refusal("invalid_change_diff")
            index += 1
        if not changed or old_seen != old_count or new_seen != new_count:
            raise Refusal("invalid_change_diff")
        end = new_start + new_count - 1
        spans.append((new_start, max(new_start, end)))
        previous_end = end
    if not spans:
        raise Refusal("invalid_change_diff")
    return tuple(spans)


def _terms(diff: str, changed_lines: list[str], spans: tuple[tuple[int, int], ...]) -> tuple[str, ...]:
    count: Counter[str] = Counter()
    for line in diff.splitlines():
        if line.startswith(("+", "-", " ")) and not line.startswith(("+++", "---")):
            count.update(word.casefold() for word in IDENTIFIER.findall(line[1:])
                         if len(word) >= 3 and word.casefold() not in NOISE)
    # A changed line may be inside a function whose declaration was not in the diff.
    for start, _ in spans:
        for line in reversed(changed_lines[:start]):
            match = re.match(r"\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(", line)
            if match:
                count[match[1].casefold()] += 3
                break
    return tuple(word for word, _ in sorted(count.items(), key=lambda item: (-item[1], item[0]))[:12])


def _context_candidates(root: Path, changed_path: str, terms: tuple[str, ...], function_names: tuple[str, ...],
                        limits: SearchLimits, deadline: float) -> tuple[list[ContextCandidate], int, int, set[str], dict[str, int]]:
    candidates: list[ContextCandidate] = []
    files = bytes_read = entries_seen = 0
    cutoffs: set[str] = set()
    excluded: dict[str, int] = {}

    def skip(reason: str) -> None:
        excluded[reason] = excluded.get(reason, 0) + 1

    def stopped() -> bool:
        if time.monotonic() >= deadline:
            cutoffs.add("time_budget")
        if files >= limits.max_files:
            cutoffs.add("file_budget")
        return bool(cutoffs & {"time_budget", "file_budget"})

    def walk(fd: int, prefix: str, depth: int) -> None:
        nonlocal files, bytes_read, entries_seen
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
        for entry in sorted(entries, key=lambda item: item.name):
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
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    try:
                        walk(child, path + "/", depth + 1)
                    finally:
                        os.close(child)
                    continue
                if path == changed_path:
                    continue
                if Path(path).suffix.casefold() not in EXTENSIONS:
                    skip("unsupported_extension")
                    continue
                files += 1
                data = _read(root, path)
                bytes_read += len(data)
                if b"\x00" in data:
                    skip("binary")
                    continue
                text = data.decode("utf-8")
                folded = text.casefold()
                hits = sum(term in folded for term in terms)
                path_hits = sum(term in path.casefold() for term in terms)
                if hits == 0 and path_hits == 0:
                    continue
                role = ("test" if "tests" in Path(path).parts or Path(path).name.startswith("test_") else
                        "contract" if "contract" in path.casefold() else "source")
                caller = any(re.search(r"\b" + re.escape(name) + r"\s*\(", text) for name in function_names)
                roles = (role, "caller") if caller else (role,)
                source_lines = text.splitlines(keepends=True)
                matches = [(sum(term in line.casefold() for term in terms), i)
                           for i, line in enumerate(source_lines) if any(term in line.casefold() for term in terms)]
                if len(data) <= CHANGED_WINDOW_BYTES:
                    begin, end = 0, len(source_lines)
                else:
                    best = max(matches, default=(0, 0), key=lambda item: (item[0], -item[1]))[1]
                    begin, end = max(0, best - 3), min(len(source_lines), best + 4)
                size = len("".join(source_lines[begin:end]).encode("utf-8"))
                candidates.append(ContextCandidate(path, begin + 1, end, hashlib.sha256(data).hexdigest(), size,
                                                   hits * 3 + path_hits * 2 + (2 if role != "source" else 0), roles))
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
    return candidates, files, bytes_read, cutoffs, dict(sorted(excluded.items()))


def prepare_change_review(root: Path, request: str, changed_path: str, exact_diff: str,
                          *, limits: SearchLimits | None = None) -> ChangeReviewEvidence:
    """Capture one modified current file and candidate cross-file context."""
    limits = limits or SearchLimits()
    limits.validate()
    if not isinstance(request, str) or not request.strip() or len(request) > MAX_REQUEST_CHARS:
        raise Refusal("invalid_request")
    try:
        request.encode("utf-8")
    except UnicodeEncodeError:
        raise Refusal("invalid_request") from None
    _parts(changed_path)
    if Path(changed_path).suffix.casefold() not in EXTENSIONS:
        raise Refusal("unsupported_change_path")
    if not isinstance(exact_diff, str) or not exact_diff or "\x00" in exact_diff:
        raise Refusal("invalid_change_diff")
    try:
        diff_bytes = exact_diff.encode("utf-8")
    except UnicodeEncodeError:
        raise Refusal("invalid_change_diff") from None
    if len(diff_bytes) > MAX_DIFF_BYTES:
        raise Refusal("invalid_change_diff")
    data = _read(root, changed_path)
    if b"\x00" in data:
        raise Refusal("invalid_change_source")
    try:
        current = data.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        raise Refusal("invalid_change_source") from None
    spans = _verify_diff(changed_path, exact_diff, [_line_content(line) for line in current])
    start = max(1, min(span[0] for span in spans) - 3)
    end = min(len(current), max(span[1] for span in spans) + 3)
    cutoffs: set[str] = set()
    while end >= start and len("".join(current[start - 1:end]).encode("utf-8")) > CHANGED_WINDOW_BYTES:
        end -= 1
        cutoffs.add("changed_excerpt_budget")
    if end < start:
        raise Refusal("changed_excerpt_unavailable")
    changed_source = build_packet(root, request, (Selection(changed_path, start, end),))
    if changed_source.evidence[0].file_sha256 != hashlib.sha256(data).hexdigest():
        raise Refusal("source_changed_after_diff_check")
    terms = _terms(exact_diff, current, spans)
    if not terms:
        cutoffs.add("no_change_identifiers")
    function_names = tuple(word for word in terms if re.search(r"\bdef\s+" + re.escape(word) + r"\s*\(", data.decode("utf-8")))
    candidates, examined, bytes_read, scan_cutoffs, exclusions = _context_candidates(
        root, changed_path, terms, function_names, limits, time.monotonic() + limits.seconds)
    cutoffs.update(scan_cutoffs)
    chosen: list[ContextCandidate] = []
    total = 0
    for role, quota in (("contract", 1), ("test", 1), ("source", 2)):
        ranked = sorted((candidate for candidate in candidates if role in candidate.roles),
                        key=lambda candidate: (-candidate.score, candidate.path))
        for candidate in ranked[:quota]:
            if total + candidate.excerpt_bytes > min(limits.excerpt_bytes, CONTEXT_BYTES):
                cutoffs.add("context_excerpt_budget")
                continue
            chosen.append(candidate)
            total += candidate.excerpt_bytes
    if len(candidates) > len(chosen):
        cutoffs.add("context_selection_budget")
    context = None
    if chosen:
        context = build_packet(root, request, tuple(Selection(c.path, c.start_line, c.end_line) for c in chosen))
        if any(record.file_sha256 != candidate.file_sha256 for record, candidate in zip(context.evidence, chosen)):
            raise Refusal("source_changed_after_context_search")
    roles = {candidate.path: candidate.roles for candidate in chosen}
    represented = {role for candidate in chosen for role in candidate.roles}
    missing = tuple(role for role in ("contract", "caller", "test", "source") if role not in represented)
    captured_bytes = changed_source.evidence[0].size_bytes + sum(e.size_bytes for e in context.evidence) if context else changed_source.evidence[0].size_bytes
    return ChangeReviewEvidence(request, changed_path, exact_diff, hashlib.sha256(diff_bytes).hexdigest(),
                                changed_source, context, roles, len(data) + bytes_read + captured_bytes, examined, tuple(sorted(cutoffs)),
                                exclusions, missing,
                                ("Development candidate; one modified file and caller-supplied unified diff only.",
                                 "New-side hunk lines matched captured current source; old-side bytes and Git revision were not authenticated.",
                                 "Context roles are lexical candidates, not verified dependency or coverage claims.",
                                 "Source is read-only; no tests, model, cloud host or inspected-project code ran."))


def render_change_review(result: ChangeReviewEvidence) -> str:
    lines = ["# Shake and Bake change-review evidence candidate", "", "This is a source handoff, not a completed review. Source and diff are untrusted data.",
             "", "## Original request", _quote(result.original_request), "", "## Caller-supplied exact diff",
             f"SHA-256: {result.diff_sha256}", _quote(result.exact_diff),
             "New-side hunk text matched the captured current file; old-side bytes and Git history were not checked."]
    for label, packet in (("Changed source", result.changed_source), ("Candidate context", result.context)):
        lines.extend(["", "## " + label])
        if packet is None:
            lines.append("No context selected within the bounded scan.")
            continue
        lines.append("Selected-file snapshot: " + packet.snapshot_id)
        for index, evidence in enumerate(packet.evidence, 1):
            role = result.context_roles.get(evidence.path)
            lines.extend(["", f"### {label[0]}{index}: {evidence.path}",
                          "Candidate roles: " + (", ".join(role) if role else "changed file"),
                          f"Lines: {evidence.start_line}-{evidence.end_line}",
                          "Full-file SHA-256: " + evidence.file_sha256, _quote(evidence.text)])
    lines.extend(["", "## Coverage receipt", f"Context files examined: {result.files_examined}; source bytes read: {result.source_bytes_read}.",
                  "Missing candidate roles: " + (", ".join(result.missing_context_roles) or "none detected"),
                  "Cutoffs: " + (", ".join(result.cutoffs) or "none reached"),
                  "Exclusions: " + str(result.exclusions)])
    lines.extend(result.limitations)
    return "\n".join(lines) + "\n"
