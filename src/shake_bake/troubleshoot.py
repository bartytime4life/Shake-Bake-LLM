"""Locate pasted failures in approved source without running that source.

Traceback paths and statements are claims made by the pasted text. A captured
frame records current bytes; even a matching statement does not prove the paste
came from this checkout, interpreter or revision.
"""

from dataclasses import asdict
import hashlib
import json
import errno
import os
from pathlib import Path, PurePosixPath
import re
import stat

from .collector import _parts, _read
from .contracts import Evidence, Refusal
from .error_formats import parse_javascript, strip_terminal_controls
from .pytest_formats import parse_pytest
from .screening import screen_failure
from .search import EXCLUDED_DIRS


MAX_ERROR_BYTES = 65_536
MAX_COMMAND_BYTES = 4_096
MAX_WORKING_DIRECTORY_BYTES = 4_096
MAX_EXCEPTION_MESSAGE_BYTES = 2_048
MAX_FRAMES = 20
MAX_EVIDENCE = 10
MAX_EVIDENCE_BYTES = 16_384
CONTEXT_LINES = 3

_FRAME = re.compile(r'^  File "(.+)", line ([1-9][0-9]{0,9})(?:, in (.*))?$')
_EXCEPTION = re.compile(r'^([A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*)(?:: (.*))?$')
_EXCEPTION_ONLY_TYPES = frozenset("""
ArithmeticError AssertionError AttributeError BaseException BlockingIOError
BrokenPipeError BufferError ChildProcessError ConnectionAbortedError
ConnectionError ConnectionRefusedError ConnectionResetError EOFError
Exception FileExistsError FileNotFoundError FloatingPointError GeneratorExit
ImportError IndentationError IndexError InterruptedError IsADirectoryError
JSONDecodeError KeyboardInterrupt KeyError LookupError MemoryError
ModuleNotFoundError NameError NotADirectoryError NotImplementedError OSError
OverflowError PermissionError ProcessLookupError RecursionError ReferenceError
RuntimeError StopAsyncIteration StopIteration SyntaxError SystemError
SystemExit TabError TimeoutError TypeError UnboundLocalError UnicodeDecodeError
UnicodeEncodeError UnicodeError UnicodeTranslateError ValueError ZeroDivisionError
""".split())
_CHAIN_MARKERS = {
    "During handling of the above exception, another exception occurred:": "during_handling",
    "The above exception was the direct cause of the following exception:": "direct_cause",
}


def _lines(text: str) -> list[str]:
    """Python source line numbers use universal newlines, not Unicode separators."""
    return re.findall(r"[^\r\n]*(?:\r\n|\r|\n|$)", text)[:-1]


def _source_lines(text: str, format_name: str | None) -> list[str]:
    if format_name in ("node", "typescript"):
        # ECMAScript also counts the Unicode line/paragraph separators. Do not
        # use splitlines(), which would incorrectly count formfeed and others.
        return re.findall(r"[^\r\n\u2028\u2029]*(?:\r\n|\r|\n|\u2028|\u2029|$)", text)[:-1]
    return _lines(text)


def _input(value: str, limit: int, code: str, *, required: bool = False) -> None:
    if not isinstance(value, str) or (required and not value.strip()) or "\x00" in value:
        raise Refusal(code)
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        raise Refusal(code) from None
    if size > limit:
        raise Refusal(code)


def _parse(error_output: str) -> tuple[list[dict], list[dict], list[dict], list[str], int]:
    lines = [line.rstrip("\r\n") for line in _lines(error_output)]
    frames: list[dict] = []
    exceptions: list[dict] = []
    relations: list[dict] = []
    cutoffs: set[str] = set()
    chain = 0
    in_traceback = False
    saw_traceback = False
    block_started = False
    pending_chain_block = False
    frame_number = 0

    def start_block() -> None:
        nonlocal chain, block_started, pending_chain_block
        # Logs and test runners can contain several independent failures. Their
        # locations must not be presented as frames of the final failure. An
        # explicit cause/handling marker has already advanced the chain once.
        if block_started and not pending_chain_block:
            chain += 1
        block_started = True
        pending_chain_block = False

    for index, line in enumerate(lines):
        if line == "Traceback (most recent call last):":
            start_block()
            in_traceback = saw_traceback = True
            continue
        if line in _CHAIN_MARKERS:
            relations.append({"from_chain": chain, "to_chain": chain + 1,
                              "relation": _CHAIN_MARKERS[line]})
            chain += 1
            in_traceback = False
            pending_chain_block = True
            continue
        match = _FRAME.fullmatch(line)
        if match:
            # A standalone File block is also how Python displays SyntaxError.
            if not in_traceback:
                start_block()
            in_traceback = saw_traceback = True
            statement = None
            if index + 1 < len(lines):
                following = lines[index + 1]
                if following.startswith("    ") and following.strip() and not _FRAME.fullmatch(following):
                    if not re.fullmatch(r"[\s~^]+", following):
                        statement = following[4:]
            frame_number += 1
            frames.append({"frame_id": f"F{frame_number}", "chain_index": chain,
                           "reported_path": match[1], "line": int(match[2]),
                           "function": match[3], "statement": statement,
                           "path": None, "status": "not_checked", "source_comparison": "unknown",
                           "evidence_id": None})
            if len(frames) > MAX_FRAMES:
                frames.pop(0)
                cutoffs.add("frame_budget")
            continue
        match = _EXCEPTION.fullmatch(line)
        if match and (in_traceback or (not saw_traceback and match[1].rsplit(".", 1)[-1] in _EXCEPTION_ONLY_TYPES)):
            # Only an unindented terminal line is interpreted. The full paste,
            # including multiline messages and notes, remains untouched below.
            message = match[2] or ""
            message_bytes = message.encode("utf-8")
            clipped = len(message_bytes) > MAX_EXCEPTION_MESSAGE_BYTES
            if clipped:
                # Derived display metadata may be shortened; the exact pasted
                # error is retained independently. Avoid repeating a 64-KiB
                # control-heavy message three times through JSON transport.
                message = message_bytes[:MAX_EXCEPTION_MESSAGE_BYTES].decode("utf-8", errors="ignore")
                cutoffs.add("exception_message_budget")
            exceptions.append({"chain_index": chain, "type": match[1], "message": message,
                               "message_bytes": len(message_bytes), "message_truncated": clipped})
            if len(exceptions) > MAX_FRAMES:
                exceptions.pop(0)
                cutoffs.add("exception_budget")
            in_traceback = False
            block_started = True
            pending_chain_block = False
    if len(relations) > MAX_FRAMES:
        relations = relations[-MAX_FRAMES:]
        cutoffs.add("chain_budget")
    return frames, exceptions, relations, sorted(cutoffs), chain


def _working_directory(root: Path, supplied: str) -> str:
    """Validate an explicitly selected directory without following symlinks."""
    _input(supplied, MAX_WORKING_DIRECTORY_BYTES, "invalid_failure_working_directory")
    if ".." in supplied.split("/"):
        raise Refusal("working_directory_not_allowed")
    path = PurePosixPath(supplied or ".")
    if path.is_absolute():
        try:
            path = path.relative_to(PurePosixPath(root))
        except ValueError:
            raise Refusal("working_directory_outside_project") from None
    relative = path.as_posix()
    if relative == ".":
        parts = ()
    else:
        try:
            parts = _parts(relative)
        except Refusal:
            raise Refusal("working_directory_not_allowed") from None
        if any(part in EXCLUDED_DIRS for part in parts):
            raise Refusal("working_directory_not_allowed")
    # Even '.' must be an actual approved directory. Never resolve() here:
    # resolving would hide a symlink and turn it into permission to read files.
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise Refusal("unsupported_read_boundary")
    descriptors = []
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        if stat.S_ISLNK(os.stat(root, follow_symlinks=False).st_mode):
            raise Refusal("working_directory_not_allowed")
        parent = os.open(root, flags)
        descriptors.append(parent)
        for part in parts:
            if stat.S_ISLNK(os.stat(part, dir_fd=parent, follow_symlinks=False).st_mode):
                raise Refusal("working_directory_not_allowed")
            parent = os.open(part, flags, dir_fd=parent)
            descriptors.append(parent)
    except OSError as error:
        # O_NOFOLLOW still refuses a directory replaced after the stat check;
        # no path resolution or symlink target read grants additional access.
        code = ("working_directory_not_allowed" if error.errno == errno.ELOOP
                else "working_directory_unavailable")
        raise Refusal(code) from None
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
    return relative


def _relative_path(root: Path, reported: str, working_directory_path: str = ".") -> str:
    # Reject traversal before PurePosixPath can normalize components. In
    # particular an absolute in-root prefix must not authorize ../outside.
    if ".." in reported.split("/"):
        raise Refusal("path_not_allowed")
    path = PurePosixPath(reported)
    if path.is_absolute():
        try:
            path = path.relative_to(PurePosixPath(root))
        except ValueError:
            raise Refusal("outside_project") from None
    elif working_directory_path != ".":
        path = PurePosixPath(working_directory_path) / path
    relative = path.as_posix()
    _parts(relative)
    return relative


def _guidance(terminal: dict | None, primary: dict | None, frames: list[dict]) -> list[dict]:
    guidance = []
    if primary:
        guidance.append({"title": "Start at the innermost project frame",
                         "detail": f"{primary['frame_id']} is the innermost captured project frame in the final traceback. "
                         "It locates where this failure surfaced; it does not establish the root cause."})
    elif frames:
        guidance.append({"title": "Confirm the project used by the failed run",
                         "detail": "No frame in the final traceback was captured in this approved project. "
                         "Check the reported paths and selected project; external files were not opened and filenames were not guessed."})
    if any(frame["source_comparison"] == "mismatch" for frame in frames):
        guidance.append({"title": "Check that the source matches the failed run",
                         "detail": "At least one pasted statement differs from the current source at that line. "
                         "Confirm the checkout and version used by the failed command before relying on these locations."})
    if not terminal:
        guidance.append({"title": "Include the complete Python error",
                         "detail": "Paste from the Traceback line through the final exception. Other log formats and truncated "
                         "or decorated tracebacks may not be recognized. No cause was inferred from the log."})
        return guidance
    kind = terminal["type"].rsplit(".", 1)[-1]
    if kind in ("ModuleNotFoundError", "ImportError"):
        guidance.append({"title": "Check the interpreter and import path",
                         "detail": "Python reports an import failure. The paste does not establish whether an installed package "
                         "is missing, a local module is unavailable, or the command used a different interpreter or working directory. "
                         "Confirm that environment before installing anything."})
    elif kind in ("SyntaxError", "IndentationError", "TabError"):
        detail = ("The reported statement matches current source. Inspect the reported syntax and nearby lines; "
                  "the parser location can be after the underlying mistake." if primary and primary["source_comparison"] == "match" else
                  "Inspect the file and line reported by Python, first confirming that they match the version from the failed run. "
                  "The parser location can be after the underlying mistake.")
        guidance.append({"title": "Inspect the reported syntax location", "detail": detail})
    elif kind == "JSONDecodeError":
        guidance.append({"title": "Check the JSON input from that run",
                         "detail": "Python reports invalid JSON. Line and column values in the exception refer to the JSON input, "
                         "not necessarily to the Python source line. This report has not read or validated that input."})
    elif kind == "PermissionError":
        guidance.append({"title": "Check the resource and required access",
                         "detail": "The exception reports an operating-system access denial. This report does not establish the account, "
                         "resource permissions, or a safe permission change. Verify those details for the failed command."})
    elif kind == "FileNotFoundError":
        guidance.append({"title": "Check the missing path and working directory",
                         "detail": "The exception reports a missing path. Relative paths depend on the failed process's working directory; "
                         "confirm that it matches the owner-selected directory used for source lookup. This report does not prove that a file should be created."})
    else:
        guidance.append({"title": "Use the exception with the captured source",
                         "detail": ("Read the final exception alongside the innermost project frame and its callers. "
                                    if primary else "Confirm the project and source locations used by the failed run before investigating the exception. ")
                         + "The exception text and locations are evidence for investigation, not a verified diagnosis or fix."})
    return guidance


def _javascript_guidance(format_name: str, terminal: dict | None,
                         primary: dict | None, frames: list[dict]) -> list[dict]:
    guidance = []
    if primary:
        guidance.append({"title": "Inspect this compiler location" if format_name == "typescript" else "Start at the first project frame",
                         "detail": ("This is the first readable compiler location in the selected project. Read its corresponding diagnostic and nearby declarations."
                                    if format_name == "typescript" else
                                    "Node.js lists the innermost call first. This is the first readable project frame; inspect its callers and the error message too.")})
    else:
        guidance.append({"title": "Check the selected project and reported paths",
                         "detail": "No readable project location was captured. Connect the exact source used by the failed run; external paths, browser URLs and runtime internals are not opened."})
    if format_name == "typescript":
        guidance.append({"title": "Check the compiler context before changing types",
                         "detail": "Confirm the TypeScript version, project configuration and full diagnostic from the failed build. A diagnostic location does not establish the correct type, dependency version or fix. No compiler was run by this check."})
    elif terminal and (terminal.get("code") in ("MODULE_NOT_FOUND", "ERR_MODULE_NOT_FOUND")
                       or "Cannot find module" in terminal.get("message", "")):
        guidance.append({"title": "Check the import and runtime environment",
                         "detail": "Confirm the import spelling, module mode, working directory and dependency installation used by the failed Node.js process. The log alone does not establish that installing a package is the right fix."})
    elif terminal and terminal["type"].rsplit(".", 1)[-1] == "SyntaxError":
        guidance.append({"title": "Check the syntax and runtime module mode",
                         "detail": "Inspect the reported line and preceding code, then confirm the Node.js version and whether the file was loaded as CommonJS or an ES module. The parser location may follow the underlying mistake."})
    else:
        guidance.append({"title": "Trace the value and its callers",
                         "detail": "Read the error with the captured expression and its callers. Determine which input or state produced the failure before proposing a change. This report has not run or verified a fix."})
    if any(frame.get("path_status") in ("remote_url", "unsupported_location", "invalid_file_url") for frame in frames):
        guidance.append({"title": "Use local source locations",
                         "detail": "Some frames refer to browser URLs or unsupported locations. No network request or source-map lookup was made. A matching local path must be supplied explicitly by the error or compiler output."})
    return guidance


def locate_failure(root: Path, error_output: str, command: str = "", *, working_directory: str = "") -> dict:
    """Return a bounded current-source location report; make no model calls or writes."""
    _input(error_output, MAX_ERROR_BYTES, "invalid_error_output", required=True)
    _input(command, MAX_COMMAND_BYTES, "invalid_failure_command")
    try:
        root = Path(root)
    except (TypeError, ValueError):
        raise Refusal("invalid_project_root") from None
    if not root.is_absolute() or ".." in root.parts:
        raise Refusal("invalid_project_root")
    working_directory_path = _working_directory(root, working_directory)
    pytest = parse_pytest(error_output)
    if pytest["format"]:
        # Decorated report boundaries take precedence over tracebacks that may
        # occur inside captured test output. Raw input remains independent.
        frames, exceptions, relations, parsed_cutoffs = (pytest[key] for key in ("frames", "exceptions", "chain_relations", "cutoffs"))
        parsed_final_chain = pytest["last_chain"]
        format_name = "pytest"
    else:
        frames, exceptions, relations, parsed_cutoffs, parsed_final_chain = _parse(strip_terminal_controls(error_output))
        format_name = "python" if frames or exceptions else None
        javascript = parse_javascript(error_output)
        if not frames and javascript["format"] and (javascript["frames"] or not exceptions or javascript["format"] == "typescript"):
            frames, exceptions, relations, parsed_cutoffs = (javascript[key] for key in ("frames", "exceptions", "chain_relations", "cutoffs"))
            format_name = javascript["format"]
    cutoffs = set(parsed_cutoffs)
    evidence: list[dict] = []
    cached: dict[str, tuple[bytes, list[str]]] = {}
    selected: dict[tuple[str, int], dict] = {}
    total_bytes = 0
    # Python prints outermost first; V8 and compiler diagnostics put the first
    # location to investigate first. Keep that order when capture is capped.
    capture_order = list(reversed(frames)) if format_name in ("python", "pytest") else frames
    for frame in capture_order:
        if frame.get("path_status", "not_checked") != "not_checked":
            frame["status"] = frame["path_status"]
            continue
        try:
            path = _relative_path(root, frame.get("lookup_path") or frame["reported_path"], working_directory_path)
            frame["path"] = path
            key = (path, frame["line"])
            if key not in selected and len(evidence) >= MAX_EVIDENCE:
                cutoffs.add("capture_budget")
                frame["status"] = "capture_budget"
                continue
            if path not in cached:
                data = _read(root, path)
                if b"\x00" in data:
                    raise Refusal("text_file_required")
                try:
                    source_lines = _source_lines(data.decode("utf-8"), format_name)
                except UnicodeDecodeError:
                    raise Refusal("utf8_required") from None
                cached[path] = (data, source_lines)
            data, source_lines = cached[path]
            target = frame["line"] - 1
            exception_index = frame.get("exception_index")
            bound_exception = (exceptions[exception_index] if type(exception_index) is int
                               and 0 <= exception_index < len(exceptions) else None)
            end_of_file = (format_name == "node" and frame.get("column") is None and source_lines
                           and target == len(source_lines) and source_lines[-1].endswith(("\n", "\r", "\u2028", "\u2029"))
                           and bound_exception and bound_exception["type"] == "SyntaxError"
                           and bound_exception["message"] == "Unexpected end of input")
            if end_of_file:
                # V8 can point one line past the final newline. Qualify each
                # frame before sharing captured context with an alias path.
                target -= 1
            if not 0 <= target < len(source_lines):
                raise Refusal("line_out_of_range")
            if key in selected:
                record = selected[key]
            else:
                begin, end = max(0, target - CONTEXT_LINES), min(len(source_lines), target + CONTEXT_LINES + 1)
                while len("".join(source_lines[begin:end]).encode("utf-8")) > MAX_EVIDENCE_BYTES - total_bytes:
                    if begin == target and end == target + 1:
                        raise Refusal("excerpt_budget")
                    if target - begin >= end - target - 1 and begin < target:
                        begin += 1
                    else:
                        end -= 1
                    cutoffs.add("context_excerpt_budget")
                excerpt = "".join(source_lines[begin:end])
                captured = Evidence(path, begin + 1, end, excerpt, hashlib.sha256(data).hexdigest(),
                                    hashlib.sha256(excerpt.encode("utf-8")).hexdigest(), len(data))
                record = {"evidence_id": f"E{len(evidence) + 1}", **asdict(captured)}
                evidence.append(record)
                selected[key] = record
                total_bytes += len(excerpt.encode("utf-8"))
            if end_of_file:
                frame["location_kind"] = "end_of_file"
                frame["context_line"] = len(source_lines)
            if frame["statement"] is not None:
                source_line = cached[path][1][frame["line"] - 1].rstrip("\r\n")
                # Python's traceback formatter strips both ends of its derived
                # statement. Compare that representation, preserving exact
                # original source and pasted output independently above.
                frame["source_comparison"] = ("match" if frame["statement"].strip() == source_line.strip() else "mismatch")
            frame["status"] = "located"
            frame["evidence_id"] = record["evidence_id"]
        except Refusal as refusal:
            frame["status"] = refusal.code
            if refusal.code == "excerpt_budget":
                cutoffs.add("evidence_byte_budget")
    final_chain = max([item["chain_index"] for item in frames + exceptions]
                      + [item["to_chain"] for item in relations]
                      + [parsed_final_chain if format_name in ("python", "pytest") else 0])
    terminal = exceptions[-1] if exceptions and exceptions[-1]["chain_index"] == final_chain else None
    primary = next((frame for frame in capture_order
                    if frame["chain_index"] == final_chain and frame["status"] == "located"), None)
    if format_name in ("node", "typescript"):
        terminal = javascript["terminal_exception"]
        if primary is not None:
            exception_index = primary.get("exception_index")
            terminal = (exceptions[exception_index] if type(exception_index) is int
                        and 0 <= exception_index < len(exceptions) else None)
    guidance = (_javascript_guidance(format_name, terminal, primary, frames)
                if format_name in ("node", "typescript") else _guidance(terminal, primary, frames))
    if format_name == "node" and any("aggregate_parent_index" in item for item in exceptions):
        guidance.append({"title": "Review aggregate members separately",
                         "detail": "This Node.js AggregateError groups separate errors. Each supported member's frames are associated with that member's message; the array order does not establish a cause or a sequence of failures. Read the aggregate and other members in the original error too."})
    if "node_aggregate_format_unsupported" in cutoffs:
        guidance.insert(0, {"title": "Part of this Node.js error could not be interpreted",
                            "detail": "A nested, incomplete or unsupported aggregate structure remains in the original error. Unrecognized member frames were not captured or assigned another error's message. Use the full original output when investigating; this report covers only supported locations."})
    if format_name == "pytest":
        guidance = [{"title": "Review the final pytest failure and its callers",
                     "detail": "The main result refers to the final failure section. Other captured tests and callers are in matching details. Confirm the exact test, input and environment before changing code; no tests were run by this check."}]
        if not terminal or "pytest_traceback_format_unsupported" in cutoffs or "pytest_incomplete_case" in cutoffs:
            guidance.append({"title": "Use a complete supported pytest report",
                             "detail": "Include the FAILURES or ERRORS section, test headings and full locations. Default, long and short decorated tracebacks are supported. Abbreviated, tree-shaped or truncated reports may remain incomplete; no missing paths or errors were guessed."})
        if any(frame["source_comparison"] == "mismatch" for frame in frames):
            guidance.append({"title": "Confirm the source used by that test run",
                             "detail": "A displayed statement differs from the current file. Check the checkout and version used by the failed tests before relying on these locations."})
    snapshot = hashlib.sha256(json.dumps([(item["path"], item["file_sha256"], item["start_line"], item["end_line"])
                                         for item in evidence], separators=(",", ":")).encode("utf-8")).hexdigest()
    report = {"schema_version": "0.1", "kind": "failure_source_report", "outcome": "ANSWER" if evidence else "ABSTAIN",
            "command": command, "error_output": error_output, "error_sha256": hashlib.sha256(error_output.encode("utf-8")).hexdigest(),
            "working_directory": working_directory, "working_directory_path": working_directory_path,
            "supported_format": bool(frames or exceptions), "format": format_name, "source_located": bool(evidence), "frames": frames,
            "evidence": evidence, "exceptions": exceptions, "terminal_exception": terminal,
            "innermost_project_frame": primary["frame_id"] if primary else None, "chain_relations": relations,
            "snapshot_id": snapshot, "selected_excerpt_bytes": total_bytes,
            "cutoffs": sorted(cutoffs), "guidance": guidance,
            "limitations": ["Current source location only; the failure's root cause and fix are unverified.",
                            "Pasted paths, statements, commands and exception messages are untrusted data; nothing was executed.",
                            "A location or matching statement does not prove the failed run used this checkout or file version.",
                            "Generated files are read as reported; no source maps or path translations were inferred.",
                            "Only exact paths in the approved project are read; no basename guessing or external-file access.",
                            "Relative source locations use only the explicitly selected working directory, defaulting to the approved project root; no directory was inferred from the command or log.",
                            "No tests, dependency checks, model calls, installation or source changes were performed."]}
    report["screening"] = screen_failure(report)
    if any(frame.get("location_kind") == "end_of_file" for frame in frames):
        report["limitations"].append("An end-of-file location can be one line after the last stored source line; captured preceding context is labelled separately from the reported line.")
    return report
