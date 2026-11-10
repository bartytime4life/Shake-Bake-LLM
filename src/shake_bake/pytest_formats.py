"""Bounded location claims from ordinary decorated pytest failure reports.

Only pytest's report section and case framing enable decorated locations. The
parser does not import pytest, read paths or execute a test. Terminal controls
are removed from a matching copy; callers retain the original error unchanged.
Native Python tracebacks are left to the ordinary Python parser when safe to do
so. Tree-shaped exception groups and abbreviated reports are explicit gaps.
"""

import re

from .contracts import Refusal
from .error_formats import strip_terminal_controls


MAX_ERROR_BYTES = 65_536
MAX_FRAMES = 20
MAX_EXCEPTIONS = 20
MAX_RELATIONS = 20
MAX_MESSAGE_BYTES = 2_048

_SECTION = re.compile(r"^={3,} (?:FAILURES|ERRORS) ={3,}$")
_SUMMARY = re.compile(r"^={3,} short test summary info ={3,}$")
_SUMMARY_ITEM = re.compile(r"^(?:FAILED|ERROR) \S.*$")
_CASE = re.compile(r"^_+ (?P<title>\S(?:.*\S)?) _+$")
_CAPTURE = re.compile(r"^-{3,} Captured (?:stdout|stderr|log)(?: (?:setup|call|teardown))? -{3,}$")
_POSITION = r"[1-9][0-9]{0,9}"
_TYPE = r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*"
_SHORT_LOCATION = re.compile(rf"^(?P<path>.+):(?P<line>{_POSITION}): in (?P<function>\S.*)$")
_LONG_LOCATION = re.compile(rf"^(?P<path>.+):(?P<line>{_POSITION}):[ \t]*(?P<type>{_TYPE})?[ \t]*$")
_E_SYNTAX_FILE = re.compile(rf'^E[ \t]+File "(?P<path>.+)", line (?P<line>{_POSITION})$')
_E_LINE = re.compile(r"^E[ \t]+(?P<body>.*)$")
_EXCEPTION = re.compile(rf"^(?P<type>{_TYPE})(?:: ?(?P<message>.*))?$")
_CARET = re.compile(r"^[ \t~^]+$")
_GROUP = re.compile(r"^[ \t]*\+ Exception Group Traceback \(most recent call last\):$")
_CHAIN = {
    "During handling of the above exception, another exception occurred:": "during_handling",
    "The above exception was the direct cause of the following exception:": "direct_cause",
}


def _exception(kind: str, message: str, chain: int, cutoffs: set[str]) -> dict:
    encoded = message.encode("utf-8")
    clipped = len(encoded) > MAX_MESSAGE_BYTES
    if clipped:
        cutoffs.add("exception_message_budget")
        message = encoded[:MAX_MESSAGE_BYTES].decode("utf-8", errors="ignore")
    return {"chain_index": chain, "type": kind, "message": message,
            "message_bytes": len(encoded), "message_truncated": clipped}


def _error_claim(line: str) -> tuple[str, str] | None:
    match = _E_LINE.fullmatch(line)
    if match is None:
        return None
    body = match["body"]
    if body == "assert" or body.startswith("assert "):
        return "AssertionError", body
    match = _EXCEPTION.fullmatch(body)
    if match:
        return match["type"], match["message"] or ""
    return None


def _frame(match: re.Match, chain: int, number: int, statement: str | None,
           function: str | None = None) -> dict:
    return {"frame_id": f"F{number}", "chain_index": chain,
            "reported_path": match["path"], "line": int(match["line"]),
            "function": function, "statement": statement, "path": None,
            "status": "not_checked", "source_comparison": "unknown", "evidence_id": None}


def parse_pytest(error_output: str) -> dict:
    """Parse default/long and short reports without guessing missing locations.

    Frames remain outermost first. Independent case headings advance the final
    chain even when the final case is incomplete or unsupported, preventing an
    earlier test's source or message from being promoted to the final failure.
    Limits retain the final frames/exceptions/relations. Captured output is
    ignored until the next report-width case heading or report section.
    """
    if not isinstance(error_output, str) or "\x00" in error_output:
        raise Refusal("invalid_error_output")
    try:
        if len(error_output.encode("utf-8")) > MAX_ERROR_BYTES:
            raise Refusal("invalid_error_output")
    except UnicodeEncodeError:
        raise Refusal("invalid_error_output") from None
    lines = re.split(r"\r\n|\r|\n", strip_terminal_controls(error_output))
    cases: list[list[str]] = []
    active: list[str] | None = None
    section_width = None
    in_capture = False
    saw_capture = False
    saw_section = False
    in_summary = False
    summary_item = False
    for line in lines:
        # Captured text can print pytest-looking summary/section banners. Such
        # text must not disable recognition of a subsequent real case heading.
        case_header = _CASE.fullmatch(line)
        is_case_header = (section_width is not None and len(line) >= section_width
                          and case_header and set(case_header["title"]) - {"_", " "})
        if in_capture and not is_case_header:
            continue
        if _SUMMARY.fullmatch(line):
            active = None
            section_width = None
            in_summary = True
            continue
        if in_summary:
            summary_item = summary_item or bool(_SUMMARY_ITEM.fullmatch(line))
        if _SECTION.fullmatch(line):
            saw_section = True
            section_width = len(line)
            active = None
            in_capture = in_summary = False
            continue
        # The width check excludes ordinary captured prose resembling a case
        # divider. This is syntactic framing, never authenticity or authority.
        if is_case_header:
            active = []
            cases.append(active)
            in_capture = False
            continue
        if active is not None and _CAPTURE.fullmatch(line):
            in_capture = saw_capture = True
            continue
        if active is not None and not in_capture:
            active.append(line)

    frames: list[dict] = []
    exceptions: list[dict] = []
    relations: list[dict] = []
    cutoffs: set[str] = set()
    result = {"format": None, "frames": frames, "exceptions": exceptions,
              "chain_relations": relations, "cutoffs": [], "last_chain": 0}
    if not saw_section and not summary_item:
        return result
    native = ["Traceback (most recent call last):" in case for case in cases]
    groups = [any(_GROUP.fullmatch(line) for line in case) for case in cases]
    if cases and all(native) and not any(groups) and not saw_capture:
        # A standard traceback remains standard Python; it requires no pytest
        # path heuristics. Captured native traces do not qualify for fallback.
        return result
    result["format"] = "pytest"
    if not cases:
        cutoffs.add("pytest_traceback_format_unsupported")
    chain = -1
    frame_number = 0
    for case, is_native, is_group in zip(cases, native, groups):
        chain += 1
        if is_native or is_group:
            cutoffs.add("pytest_traceback_format_unsupported")
            continue
        first_frame = len(frames)
        first_exception = len(exceptions)
        marked_statement = None
        error_claim = None
        short_frame = None
        short_exception = False
        skip_until = -1
        for index, line in enumerate(case):
            if index <= skip_until:
                continue
            if line in _CHAIN:
                relations.append({"from_chain": chain, "to_chain": chain + 1,
                                  "relation": _CHAIN[line]})
                chain += 1
                marked_statement = error_claim = short_frame = None
                short_exception = False
                continue
            match = _E_SYNTAX_FILE.fullmatch(line)
            if match:
                # Collection errors include a native SyntaxError File/source/
                # caret block inside E-prefixed pytest text. Require the whole
                # contiguous shape and terminal kind; an E-prefixed path alone
                # must never become an additional source location.
                body = case[index + 1:index + 4]
                source = _E_LINE.fullmatch(body[0]) if len(body) == 3 else None
                caret = _E_LINE.fullmatch(body[1]) if len(body) == 3 else None
                terminal = _error_claim(body[2]) if len(body) == 3 else None
                if (source and source["body"] and not _CARET.fullmatch(source["body"])
                        and caret and _CARET.fullmatch(caret["body"])
                        and terminal and terminal[0].rsplit(".", 1)[-1]
                        in ("SyntaxError", "IndentationError", "TabError")):
                    frame_number += 1
                    short_frame = _frame(match, chain, frame_number, source["body"])
                    frames.append(short_frame)
                    exceptions.append(_exception(*terminal, chain, cutoffs))
                    short_exception = True
                    marked_statement = error_claim = None
                    skip_until = index + 3
                else:
                    cutoffs.add("pytest_traceback_format_unsupported")
                continue
            match = _SHORT_LOCATION.fullmatch(line)
            if match:
                frame_number += 1
                short_frame = _frame(match, chain, frame_number, None, match["function"])
                frames.append(short_frame)
                marked_statement = error_claim = None
                continue
            if line.startswith(">") and len(line) > 1 and line[1] in " \t":
                if marked_statement is not None:
                    cutoffs.add("pytest_incomplete_case")
                marked_statement = line[1:].lstrip(" \t")
                error_claim = None
                short_frame = None
                continue
            claim = _error_claim(line)
            if claim is not None:
                if short_frame is not None:
                    if not short_exception:
                        exceptions.append(_exception(*claim, chain, cutoffs))
                        short_exception = True
                elif marked_statement is not None and error_claim is None:
                    error_claim = claim
                continue
            match = _LONG_LOCATION.fullmatch(line)
            if match and marked_statement is not None:
                frame_number += 1
                frames.append(_frame(match, chain, frame_number, marked_statement))
                kind = match["type"]
                if kind:
                    message = ""
                    if error_claim is not None and error_claim[0] == kind:
                        message = error_claim[1]
                    elif error_claim is not None:
                        cutoffs.add("pytest_exception_message_unavailable")
                    exceptions.append(_exception(kind, message, chain, cutoffs))
                marked_statement = error_claim = None
                continue
            if (short_frame is not None and short_frame["statement"] is None
                    and line.startswith("    ") and line.strip() and not _CARET.fullmatch(line)):
                short_frame["statement"] = line[4:]
        if marked_statement is not None or len(frames) == first_frame or len(exceptions) == first_exception:
            cutoffs.add("pytest_incomplete_case")
    if len(frames) > MAX_FRAMES:
        del frames[:-MAX_FRAMES]
        cutoffs.add("frame_budget")
    if len(exceptions) > MAX_EXCEPTIONS:
        del exceptions[:-MAX_EXCEPTIONS]
        cutoffs.add("exception_budget")
    if len(relations) > MAX_RELATIONS:
        del relations[:-MAX_RELATIONS]
        cutoffs.add("chain_budget")
    result["last_chain"] = max(chain, 0)
    result["cutoffs"] = sorted(cutoffs)
    return result
