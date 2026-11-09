"""Locate pasted failures in approved source without running that source.

Traceback paths and statements are claims made by the pasted text. A captured
frame records current bytes; even a matching statement does not prove the paste
came from this checkout, interpreter or revision.
"""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from .collector import _parts, _read
from .contracts import Evidence, Refusal
from .error_formats import parse_javascript, strip_terminal_controls


MAX_ERROR_BYTES = 65_536
MAX_COMMAND_BYTES = 4_096
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


def _parse(error_output: str) -> tuple[list[dict], list[dict], list[dict], list[str]]:
    lines = [line.rstrip("\r\n") for line in _lines(error_output)]
    frames: list[dict] = []
    exceptions: list[dict] = []
    relations: list[dict] = []
    cutoffs: set[str] = set()
    chain = 0
    in_traceback = False
    saw_traceback = False
    frame_number = 0
    for index, line in enumerate(lines):
        if line == "Traceback (most recent call last):":
            in_traceback = saw_traceback = True
            continue
        if line in _CHAIN_MARKERS:
            relations.append({"from_chain": chain, "to_chain": chain + 1,
                              "relation": _CHAIN_MARKERS[line]})
            chain += 1
            in_traceback = False
            continue
        match = _FRAME.fullmatch(line)
        if match:
            # A standalone File block is also how Python displays SyntaxError.
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
    if len(relations) > MAX_FRAMES:
        relations = relations[-MAX_FRAMES:]
        cutoffs.add("chain_budget")
    return frames, exceptions, relations, sorted(cutoffs)


def _relative_path(root: Path, reported: str) -> str:
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
                         "this report does not know that directory or prove that a file should be created."})
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


def locate_failure(root: Path, error_output: str, command: str = "") -> dict:
    """Return a bounded current-source location report; make no model calls or writes."""
    _input(error_output, MAX_ERROR_BYTES, "invalid_error_output", required=True)
    _input(command, MAX_COMMAND_BYTES, "invalid_failure_command")
    try:
        root = Path(root)
    except (TypeError, ValueError):
        raise Refusal("invalid_project_root") from None
    if not root.is_absolute() or ".." in root.parts:
        raise Refusal("invalid_project_root")
    frames, exceptions, relations, parsed_cutoffs = _parse(strip_terminal_controls(error_output))
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
    capture_order = list(reversed(frames)) if format_name == "python" else frames
    for frame in capture_order:
        if frame.get("path_status", "not_checked") != "not_checked":
            frame["status"] = frame["path_status"]
            continue
        try:
            path = _relative_path(root, frame.get("lookup_path") or frame["reported_path"])
            frame["path"] = path
            key = (path, frame["line"])
            if key in selected:
                record = selected[key]
            else:
                if len(evidence) >= MAX_EVIDENCE:
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
                if not 0 <= target < len(source_lines):
                    raise Refusal("line_out_of_range")
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
            source_line = cached[path][1][frame["line"] - 1].rstrip("\r\n")
            if frame["statement"] is not None:
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
                      + [item["to_chain"] for item in relations] + [0])
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
    snapshot = hashlib.sha256(json.dumps([(item["path"], item["file_sha256"], item["start_line"], item["end_line"])
                                         for item in evidence], separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"schema_version": "0.1", "kind": "failure_source_report", "outcome": "ANSWER" if evidence else "ABSTAIN",
            "command": command, "error_output": error_output, "error_sha256": hashlib.sha256(error_output.encode("utf-8")).hexdigest(),
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
                            "No tests, dependency checks, model calls, installation or source changes were performed."]}
