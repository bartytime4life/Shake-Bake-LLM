"""Deterministic, bounded lexical selection over a trusted local checkout."""

from collections import Counter
from dataclasses import asdict, dataclass, replace
import hashlib
import math
import os
from pathlib import Path
import re
import time

from .collector import MAX_FILES, _parts, _read, build_packet, validate_request
from .contracts import Packet, Refusal, Selection

EXTENSIONS = frozenset({".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".md", ".toml", ".yaml", ".yml", ".json", ".txt", ".c", ".h", ".cpp", ".java", ".sh", ".sql"})
# `_vendor` is pip's convention for bundled third-party copies, the same thing as `vendor`.
EXCLUDED_DIRS = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", "vendor", "_vendor", "target", ".idea", ".vscode"})
PROSE_EXTENSIONS = frozenset({".md", ".txt"})
STOP_WORDS = frozenset("the and for this that with from into about find show code where how does what review please have source function files file inspect controlling check".split())
# Words that carry little signal in a request: English function words and the
# vocabulary of issue templates. They never become search terms. Deliberately
# absent: test, tests, error, failed, log, logs, which name real things in code.
TEMPLATE_WORDS = frozenset("""
are but can cannot not you your when then than these those there here without within onto over under after before because
should would could will just also only any all some more most much many very use used using uses get got gets set
make makes made like want need needs try tried trying run ran running see seen did done doing has had having was were
been being which who why its our their them they him her his she out off per via etc one two new old same other
another still again every each first last next following above below issue issues bug bugs problem problems describe
description expected behavior behaviour actual steps reproduce reproduction screenshots screenshot additional context
environment operating system information version versions browser checklist searched existing example minimal
reproducible please thanks thank hello note report reported link links snippet output input result results install
installed installation pip conda traceback stack trace question questions feature request currently however anyone
someone something anything nothing already always never maybe might must seems seem looks look think thought
""".split()) | STOP_WORDS
URL_RE = re.compile(r"(?:https?://|www\.)\S+")
MAX_TERMS = 16


def request_terms(request: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Rank the request's words by signal and return (all ranked, the MAX_TERMS used).

    Signal is positional-independent: identifier shape (underscore, digits, inner capitals)
    counts most, then presence in the first line, repetition and length. URL fragments and
    template words are dropped. Ties keep first-appearance order, so the result is stable.
    """
    text = URL_RE.sub(" ", request)
    first_line = text.strip().split("\n", 1)[0].casefold() if text.strip() else ""
    title_words = set(re.findall(r"[a-z_][a-z_0-9]+", first_line))
    first_index: dict[str, int] = {}
    counts: Counter = Counter()
    shaped: dict[str, int] = {}
    for index, token in enumerate(re.findall(r"[A-Za-z_][A-Za-z_0-9]+", text)):
        if len(token) < 3:
            continue
        key = token.casefold()
        if key in TEMPLATE_WORDS:
            continue
        first_index.setdefault(key, index)
        counts[key] += 1
        # Code-shaped words: an underscore or an inner capital is strong; a digit is weak.
        strength = 3 if "_" in token or re.search(r"[a-z][A-Z]", token) else (1 if any(ch.isdigit() for ch in token) else 0)
        shaped[key] = max(shaped.get(key, 0), strength)

    def signal(key: str) -> int:
        # A one-line request scores every word alike, so its words keep appearance order.
        return shaped[key] + (2 if key in title_words else 0) + (1 if counts[key] > 1 else 0)

    ranked = tuple(sorted(first_index, key=lambda key: (-signal(key), first_index[key])))
    return ranked, ranked[:MAX_TERMS]
# Primary selection stays at four windows; the controlling-context pass may add
# definition windows, one usage window and one test window, in that order.
PRIMARY_FILES = 4
CONTEXT_WINDOWS = 4
CONTEXT_USAGE_WINDOWS = 1
CONTEXT_TEST_WINDOWS = 1
CONTEXT_MAP_ENTRIES = 12
DEFINITION_INDEX_ENTRIES = 16384
WINDOW_LINES = 7
assert PRIMARY_FILES + CONTEXT_WINDOWS + CONTEXT_USAGE_WINDOWS + CONTEXT_TEST_WINDOWS <= MAX_FILES
# BM25-style file scoring over the examined files: rarer request terms weigh more
# and repeated hits saturate. Length normalization is off (B = 0): the window is
# the retrieval unit, and a short file is not more relevant for being short.
BM25_K1 = 1.2
BM25_B = 0.0
# A file whose only hits are widespread terms (present in at least
# DISTRACTOR_COMMON_DF examined files), scoring under a fifth of the best file,
# is excluded as a distractor and counted in exclusions as low_signal_match.
DISTRACTOR_MIN_FILES = 8
DISTRACTOR_COMMON_DF = 8
DISTRACTOR_RATIO = 0.2
# Matched lines the excerpts did not cover, listed as line number plus a short
# text so the host need not grep a large file again. Scan facts, untrusted text.
LINE_INDEX_FILES = 6
LINE_INDEX_LINES = 12
LINE_INDEX_BYTES = 2048
LINE_INDEX_TEXT = 120
# Weight of pool-normalized embedding similarity against the pool-normalized lexical score.
RERANK_BLEND = 0.5
# A name defined in more than this many places is ambiguous and is not followed as context.
AMBIGUOUS_DEFINITIONS = 2
# Identifier names that are plain English or near-universal in code; following their
# definition rarely helps and usually lands on an unrelated assignment.
GENERIC_NAMES = frozenset("""
name names context selected value values data result results item items index count path paths text lines
line key keys config options args kwargs self cls state status type kind size total root request response
error errors message messages info meta params param entry entries record records output input label labels
""".split())
# Cutoffs that mean the scan stopped before reading everything, as opposed to selection caps.
SCAN_STOP_CUTOFFS = frozenset({"time_budget", "file_budget", "entry_budget", "depth_budget"})
IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9]{2,}")
# Top-level definitions only: a leading-column assignment or a declaration keyword.
DEFINITION_RE = re.compile(
    r"^(?:\s*(?:(?:async\s+)?def|class|function|fn|pub\s+fn|struct|enum|interface|type|"
    r"export\s+(?:default\s+)?(?:function|class|const|let|var)|const|let|var)\s+([A-Za-z_]\w*)"
    r"|([A-Za-z_]\w*)\s*(?::[^=\n]+)?=(?!=))")
KEYWORDS = frozenset(
    "def class return import from if else elif for while in not and or is none true false self cls try except "
    "finally with as lambda yield pass break continue raise assert global nonlocal async await function const let "
    "var new this typeof instanceof export default null undefined switch case int str float bool len print dict "
    "list set tuple range object super get items keys values append join split strip lower upper format".split())


def _is_test_path(path: str) -> bool:
    """A test directory, or a stem that is `test`/`tests`/`spec` or carries one as a `_` or `.` suffix or prefix;
    `contests.py` or `testament.py` are not tests."""
    parts = path.casefold().split("/")
    name = parts[-1].rsplit(".", 1)[0]
    return any(part in ("test", "tests", "spec", "specs") for part in parts[:-1]) or \
        bool(re.fullmatch(r"(tests?|specs?)(?:[_.].+)?|.+[_.](tests?|specs?)", name))


def _identifiers(text: str) -> tuple[str, ...]:
    return tuple(name for name in IDENTIFIER_RE.findall(text) if name.casefold() not in KEYWORDS)


def _first_line(lines: list[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped[:80]
    return ""


@dataclass(frozen=True)
class SearchLimits:
    # A 1,000-file walk took under half a second on the thirteen external repositories
    # (November 7). `seconds` bounds the walk; the passes after it (scoring, controlling
    # context, line index) are bounded by their own counts and bytes, and an optional
    # rerank by its own deadline, so a preparation can take longer than `seconds`.
    max_files: int = 1000
    max_entries: int = 20000
    max_depth: int = 8
    seconds: float = 5.0
    excerpt_bytes: int = 16_384
    context_bytes: int = 2048

    def validate(self) -> None:
        for name, ceiling in (("max_files", 5000), ("max_entries", 100000), ("max_depth", 16), ("excerpt_bytes", 65536)):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= ceiling:
                raise Refusal("invalid_search_limits")
        if type(self.context_bytes) is not int or not 0 <= self.context_bytes <= 16384:
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
    # Why each controlling-context excerpt was added, keyed by its evidence id,
    # and the matched files that were not excerpted. Both are software-produced
    # scan facts, not interpretations.
    context: tuple[dict, ...] = ()
    context_map: tuple[dict, ...] = ()
    # Matched lines in matched files that no excerpt covers: path, counts and short line texts.
    line_index: tuple[dict, ...] = ()
    # The optional local embedding rerank's record, or its refusal code; None when not requested.
    rerank: dict | None = None
    # Warn-only credential findings over what the brief can share (screening.py); masked previews only.
    screening: tuple[dict, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)


def prepare(root: Path, request: str, limits: SearchLimits | None = None, scorer=None) -> SearchResult:
    """`scorer(request, texts) -> similarities` optionally reorders the top lexical
    candidates before primary selection; it never adds a window the scan did not find."""
    limits = limits or SearchLimits()
    limits.validate()
    validate_request(request)
    all_terms, terms = request_terms(request)
    if not terms:
        raise Refusal("search_terms_required")
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise Refusal("unsupported_read_boundary")
    deadline = time.monotonic() + limits.seconds
    excluded: dict[str, int] = {}
    cutoffs: set[str] = set()
    if len(all_terms) > len(terms):
        cutoffs.add("query_term_budget")
    # (score, path, start_line, end_line, digest, size, rank, identifiers, text)
    candidates: list[tuple[float, str, int, int, str, int, int, tuple[str, ...], str]] = []
    examined = entries_seen = bytes_read = 0
    digests: dict[str, str] = {}
    sizes: dict[str, int] = {}
    line_counts: dict[str, int] = {}
    first_lines: dict[str, str] = {}
    file_scores: dict[str, float] = {}
    # Per matching file: its lines and the (line index, matched terms) pairs; scored after the walk.
    file_lines: dict[str, list[str]] = {}
    file_matches: dict[str, list[tuple[int, frozenset[str]]]] = {}
    path_terms: dict[str, frozenset[str]] = {}
    document_frequency: Counter = Counter()
    total_lines = 0
    definitions: dict[str, list[tuple[str, int]]] = {}
    definition_entries = 0
    names_by_file: dict[str, frozenset[str]] = {}

    def skip(reason: str) -> None:
        excluded[reason] = excluded.get(reason, 0) + 1

    def stopped() -> bool:
        if time.monotonic() >= deadline:
            cutoffs.add("time_budget")
        if examined >= limits.max_files:
            cutoffs.add("file_budget")
        return bool(cutoffs & {"time_budget", "file_budget"})

    def walk(fd: int, prefix: str, depth: int) -> None:
        nonlocal examined, entries_seen, bytes_read, definition_entries, total_lines
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
                digests[path] = hashlib.sha256(data).hexdigest()
                sizes[path] = len(data)
                line_counts[path] = len(lines)
                first_lines[path] = _first_line(lines)
                if limits.context_bytes:
                    # Prose files (Markdown, text) hold no definitions; "let the server start" is not one.
                    # They still count as places where a name is used or tested.
                    if Path(entry.name).suffix.casefold() not in PROSE_EXTENSIONS:
                        for index, line in enumerate(lines):
                            found = DEFINITION_RE.match(line)
                            if not found:
                                continue
                            name = found.group(1) or found.group(2)
                            if name.casefold() in KEYWORDS:
                                continue
                            if definition_entries >= DEFINITION_INDEX_ENTRIES:
                                cutoffs.add("definition_index_budget")
                                break
                            definitions.setdefault(name, []).append((path, index))
                            definition_entries += 1
                    names_by_file[path] = Counter(_identifiers(data.decode("utf-8")))
                total_lines += len(lines)
                matches = []
                for index, line in enumerate(lines):
                    folded = line.casefold()
                    hit = frozenset(term for term in terms if term in folded)
                    if hit:
                        matches.append((index, hit, line.strip()[:LINE_INDEX_TEXT]))
                # A request writes `MobileNetV3`; the file is `mobilenet_v3.py`. Match paths with
                # separators removed as well as literally.
                folded_path = path.casefold()
                compact_path = folded_path.replace("_", "").replace("-", "").replace(" ", "")
                in_path = frozenset(term for term in terms if term in folded_path or term.replace("_", "") in compact_path)
                if not matches and not in_path:
                    continue
                document_frequency.update(in_path.union(*(item[1] for item in matches)))
                file_lines[path] = lines
                file_matches[path] = matches
                path_terms[path] = in_path
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
    # Score matching files after the walk, when document frequencies are known.
    examined_text = max(1, len(digests))
    average_lines = total_lines / examined_text
    idf = {term: math.log(1 + (examined_text - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
           for term in terms}
    for path, matches in file_matches.items():
        frequency = Counter(term for item in matches for term in item[1])
        length = len(file_lines[path]) / average_lines if average_lines else 1.0
        file_scores[path] = sum(idf[term] * count * (BM25_K1 + 1) / (count + BM25_K1 * (1 - BM25_B + BM25_B * length))
                                for term, count in frequency.items()) + 2 * sum(idf[term] for term in path_terms[path])
    best_score = max(file_scores.values(), default=0.0)
    common = {term for term in terms if document_frequency[term] >= DISTRACTOR_COMMON_DF}
    for path in sorted(file_matches):
        matches = file_matches[path]
        matched = path_terms[path].union(*(item[1] for item in matches))
        if examined_text >= DISTRACTOR_MIN_FILES and file_scores[path] < DISTRACTOR_RATIO * best_score and matched <= common:
            skip("low_signal_match")
            del file_scores[path]
            continue
        lines = file_lines[path]
        if not lines:
            continue
        # Preserve distinct nearby evidence, including a distant branch in
        # the same file. Never replace source with a generated summary.
        windows = []
        ranked_lines = sorted(matches, key=lambda item: (-sum(idf[term] for term in item[1]), item[0])) or [(0, frozenset(), "")]
        for best, *_ in ranked_lines:
            if any(begin <= best < end for begin, end in windows):
                continue
            windows.append((max(0, best - 3), min(len(lines), best + 4)))
            if len(windows) == 2:
                break
        if any(not any(begin <= index < end for begin, end in windows) for index, *_ in matches):
            cutoffs.add("window_budget")
        for rank, (begin, end) in enumerate(windows):
            text = "".join(lines[begin:end])
            candidates.append((file_scores[path], path, begin + 1, end, digests[path], len(text.encode("utf-8")), rank, _identifiers(text), text))
    file_lines.clear()
    # Prefer one window from each file before additional windows from a file.
    lexical_key = lambda item: (item[6], -item[0], item[1], item[2])
    ordered = sorted(candidates, key=lexical_key)
    rerank_record = None
    if scorer is not None and ordered:
        from .rerank import MAX_POOL
        pool, rest = ordered[:MAX_POOL], ordered[MAX_POOL:]
        try:
            similarities = scorer(request, [item[8] for item in pool])
            if len(similarities) != len(pool) or not all(type(value) in (int, float) and -1.0001 <= value <= 1.0001 for value in similarities):
                raise Refusal("rerank_invalid_similarities")
            # Blend: half the pool-normalized similarity, half the pool-normalized lexical score, so a
            # weak prose match cannot displace a strong identifier match. One-window-per-file-first
            # still holds; the lexical key breaks ties.
            low, high = min(similarities), max(similarities)
            top = max(item[0] for item in pool) or 1.0
            blended = [RERANK_BLEND * ((value - low) / (high - low) if high > low else 1.0) + (1 - RERANK_BLEND) * (item[0] / top)
                       for value, item in zip(similarities, pool)]
            reordered = [item for _, item in sorted(zip(blended, pool), key=lambda pair: (pair[1][6], -pair[0], lexical_key(pair[1])))]
            rerank_record = {**getattr(scorer, "record", {}), "pool": len(pool), "candidates": len(candidates), "blend": RERANK_BLEND,
                             "order_changed": [c[1:4] for c in reordered] != [c[1:4] for c in pool],
                             "similarities": [round(value, 4) for value in similarities], "blended": [round(value, 4) for value in blended]}
            if rest:
                cutoffs.add("rerank_pool_budget")
            ordered = reordered + rest
        except Refusal as refusal:
            rerank_record = {**getattr(scorer, "record", {}), "pool": len(pool), "candidates": len(candidates), "error": refusal.code}
    selected = []
    total = 0
    for candidate in ordered:
        if len(selected) >= PRIMARY_FILES:
            cutoffs.add("selection_budget")
            break
        if total + candidate[5] > limits.excerpt_bytes:
            cutoffs.add("excerpt_budget")
            continue
        selected.append(candidate)
        total += candidate[5]
    selections = [Selection(c[1], c[2], c[3]) for c in selected]
    expected = [c[4] for c in selected]
    context: list[dict] = []
    context_map: list[dict] = []
    if selected and limits.context_bytes:
        context_total = 0

        def covered(path: str, index: int) -> bool:
            return any(s.path == path and s.start_line - 1 <= index < s.end_line for s in selections)

        def add_window(path: str, begin: int, end: int, reason: dict) -> bool:
            nonlocal total, context_total
            try:
                data = _read(root, path)
            except Refusal as refusal:
                skip(refusal.code)
                return False
            if hashlib.sha256(data).hexdigest() != digests[path]:
                raise Refusal("source_changed_after_search")
            lines = data.decode("utf-8").splitlines(keepends=True)
            end = min(end, len(lines))
            # Stop before an excerpt already selected from this file; never duplicate lines.
            for s in selections:
                if s.path == path and begin < s.start_line - 1 < end:
                    end = s.start_line - 1
            if begin >= end:
                return False
            size = len("".join(lines[begin:end]).encode("utf-8"))
            if total + size > limits.excerpt_bytes or context_total + size > limits.context_bytes:
                cutoffs.add("context_budget")
                return False
            selections.append(Selection(path, begin + 1, end))
            expected.append(digests[path])
            context.append({"evidence_id": f"E{len(selections)}", **reason})
            total += size
            context_total += size
            return True

        # Identifiers the selected windows use but do not define, most used first.
        mentions: dict[str, list[str]] = {}
        for number, candidate in enumerate(selected, 1):
            for name in dict.fromkeys(candidate[7]):
                if name.casefold() in terms or name not in definitions:
                    continue
                # Generic names (`name`, `files`, `context`) and names defined in several places
                # are not controlling context; following one wastes a window on a guess.
                if name.casefold() in TEMPLATE_WORDS or name.casefold() in GENERIC_NAMES or len(definitions[name]) > AMBIGUOUS_DEFINITIONS:
                    continue
                if all(covered(path, index) for path, index in definitions[name]):
                    continue
                mentions.setdefault(name, []).append(f"E{number}")
        ranked = sorted(mentions, key=lambda name: (-sum(c[7].count(name) for c in selected), name))
        added = 0
        for name in ranked:
            if added >= CONTEXT_WINDOWS:
                cutoffs.add("context_window_budget")
                break
            # Prefer a definition in the referencing file (a module constant), then path order.
            home = selected[int(mentions[name][0][1:]) - 1][1]
            for path, index in sorted(definitions[name], key=lambda place: (place[0] != home, place)):
                if covered(path, index):
                    continue
                if add_window(path, index, index + WINDOW_LINES, {"kind": "definition", "name": name, "referenced_by": mentions[name]}):
                    added += 1
                break
        # Names the selected windows define: one window where another non-test file uses each.
        defined: dict[str, str] = {}
        for name, places in definitions.items():
            for number, candidate in enumerate(selected, 1):
                if any(path == candidate[1] and candidate[2] - 1 <= index < candidate[3] for path, index in places):
                    defined.setdefault(name, f"E{number}")
        users: dict[str, list[str]] = {}
        for path, names in names_by_file.items():
            if path in {s.path for s in selections} or _is_test_path(path):
                continue
            hits = [name for name in defined if name in names]
            if hits:
                users[path] = hits
        usages = 0
        for path in sorted(users, key=lambda p: (-len(users[p]), -sum(names_by_file[p][n] for n in users[p]), p)):
            if usages >= CONTEXT_USAGE_WINDOWS:
                cutoffs.add("context_window_budget")
                break
            hits = sorted(users[path], key=lambda name: (defined[name], name))
            try:
                data = _read(root, path)
            except Refusal as refusal:
                skip(refusal.code)
                continue
            if hashlib.sha256(data).hexdigest() != digests[path]:
                raise Refusal("source_changed_after_search")
            lines = data.decode("utf-8").splitlines(keepends=True)
            index = next((i for i, line in enumerate(lines) if hits[0] in line), 0)
            if add_window(path, max(0, index - 3), index + 4, {"kind": "usage", "name": hits[0], "defined_in": defined[hits[0]]}):
                usages += 1
        # One test window naming the most selected identifiers.
        wanted = Counter()
        for candidate in selected:
            wanted.update(set(candidate[7]))
        wanted.update({item["name"]: 2 for item in context})
        scored = []
        for path, names in names_by_file.items():
            if path in {s.path for s in selections} or not _is_test_path(path):
                continue
            overlap = [name for name in wanted if name in names]
            if overlap:
                scored.append((-sum(wanted[name] for name in overlap), path, overlap))
        for _, path, overlap in sorted(scored)[:CONTEXT_TEST_WINDOWS]:
            best = sorted(overlap, key=lambda name: (-wanted[name], name))
            try:
                data = _read(root, path)
            except Refusal as refusal:
                skip(refusal.code)
                continue
            if hashlib.sha256(data).hexdigest() != digests[path]:
                raise Refusal("source_changed_after_search")
            lines = data.decode("utf-8").splitlines(keepends=True)
            index = next((i for i, line in enumerate(lines) if best[0] in line), 0)
            add_window(path, max(0, index - 3), index + 4, {"kind": "test", "names": best[:5]})
        # Matched files that were not excerpted: a map, not evidence.
        chosen = {s.path for s in selections}
        others = sorted((path for path in file_scores if path not in chosen), key=lambda p: (-file_scores[p], p))
        if len(others) > CONTEXT_MAP_ENTRIES:
            cutoffs.add("context_map_budget")
        context_map = [{"path": path, "size_bytes": sizes[path], "first_line": first_lines[path]} for path in others[:CONTEXT_MAP_ENTRIES]]
    # Matched lines no excerpt covers, most relevant files first, under byte and count bounds.
    line_index: list[dict] = []
    if selections:
        chosen = {s.path for s in selections}
        covered_lines = {(s.path, index) for s in selections for index in range(s.start_line - 1, s.end_line)}
        index_bytes = 0
        for path in sorted(file_scores, key=lambda p: (-file_scores[p], p)):
            uncovered = [item for item in file_matches[path] if (path, item[0]) not in covered_lines]
            if not uncovered:
                continue
            if len(line_index) >= LINE_INDEX_FILES:
                cutoffs.add("line_index_budget")
                break
            ranked = sorted(uncovered, key=lambda item: (-sum(idf[term] for term in item[1]), item[0]))
            entries = []
            for index, _, text in ranked[:LINE_INDEX_LINES]:
                size = len(text.encode("utf-8")) + 8
                if index_bytes + size > LINE_INDEX_BYTES:
                    cutoffs.add("line_index_budget")
                    break
                index_bytes += size
                entries.append({"line": index + 1, "text": text})
            if len(ranked) > len(entries):
                cutoffs.add("line_index_budget")
            if entries:
                line_index.append({"path": path, "excerpted": path in chosen, "total_lines": line_counts[path],
                                   "matched_lines": len(file_matches[path]), "entries": sorted(entries, key=lambda item: item["line"])})
    packet = None
    if selections:
        packet = build_packet(root, request, tuple(selections))
        if any(record.file_sha256 != digest for record, digest in zip(packet.evidence, expected)):
            raise Refusal("source_changed_after_search")
    result = SearchResult(request, packet, terms, examined, entries_seen, bytes_read, len(file_matches), total,
                          dict(sorted(excluded.items())), tuple(sorted(cutoffs)), tuple(context), tuple(context_map), tuple(line_index), rerank_record)
    from .screening import screen
    return replace(result, screening=tuple(screen(result)))
