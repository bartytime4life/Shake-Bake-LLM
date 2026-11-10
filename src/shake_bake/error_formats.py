"""Bounded JavaScript stack and TypeScript diagnostic matching.

This module interprets location claims only. It never opens paths, follows URLs,
loads source maps or runs a command. Callers retain the original pasted text and
approve every local read independently. ANSI removal affects matching only.
"""

import re
from urllib.parse import unquote, urlsplit

from .contracts import Refusal


MAX_ERROR_BYTES = 65_536
MAX_FRAMES = 20
MAX_MESSAGE_BYTES = 2_048
MAX_PATH_BYTES = 4_096
MAX_FUNCTION_BYTES = 512

# Complete CSI, OSC and terminal string sequences, including their C1 forms.
# Unclosed strings and other controls remain visible to the parser; in particular
# backspace must not silently rewrite a reported filename into a different one.
_TERMINAL = re.compile(
    r"(?:\x1b\[|\x9b)[0-?]*[ -/]*[@-~]"
    r"|(?:\x1b\]|\x9d)[^\x07\x1b\x9c]*(?:\x07|\x1b\\|\x9c)"
    r"|\x1b[P^_X][^\x1b]*(?:\x1b\\)"
    r"|\x1b[()][0-~]"
)
_POSITION = r"[1-9][0-9]{0,9}"
_LOCATION = re.compile(rf"^(?P<path>.+):(?P<line>{_POSITION}):(?P<column>{_POSITION})$")
_HEADER_LOCATION = re.compile(rf"^(?P<path>.+):(?P<line>{_POSITION})$")
_NODE_EXCEPTION = re.compile(
    r"^(?P<type>(?:[A-Za-z_$][A-Za-z_0-9$]*\.)*(?:[A-Za-z_$][A-Za-z_0-9$]*)?Error)"
    r"(?: \[(?P<code>[A-Z][A-Z_0-9]{0,79})\])?(?:: ?(?P<message>.*))?$"
)
_NODE_CAUSE = re.compile(r"^ +\[cause\]: (?P<header>.+)$")
_NODE_BRACKET_AGGREGATE = re.compile(
    r"^\[(?P<header>AggregateError(?:: ?.*)?)\] (?:\{|\{ \[errors\]: \[\] \})$"
)
_NODE_ERRORS_PROPERTY = re.compile(r"^(?P<indent> +)\[errors\]: (?P<body>.*)$")
_TS_POSITIONAL = re.compile(
    rf"^(?P<path>.+)\((?P<line>{_POSITION}),(?P<column>{_POSITION})\): "
    r"error (?P<type>TS[0-9]{3,6}): ?(?P<message>.*)$"
)
_TS_PRETTY = re.compile(
    rf"^(?P<path>.+):(?P<line>{_POSITION}):(?P<column>{_POSITION}) - "
    r"error (?P<type>TS[0-9]{3,6}): ?(?P<message>.*)$"
)
_TS_GLOBAL = re.compile(r"^error (?P<type>TS[0-9]{3,6}): ?(?P<message>.*)$")
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def strip_terminal_controls(text: str) -> str:
    """Remove terminal escapes and one initial UTF-8 BOM in a matching copy."""
    return _TERMINAL.sub("", text).removeprefix("\ufeff")


def _clip(value: str, limit: int) -> tuple[str, int, bool]:
    encoded = value.encode("utf-8")
    return (encoded[:limit].decode("utf-8", errors="ignore"), len(encoded), len(encoded) > limit)


def _exception(kind: str, message: str, cutoffs: set[str], *, code: str | None = None) -> dict:
    message, size, clipped = _clip(message, MAX_MESSAGE_BYTES)
    if clipped:
        cutoffs.add("exception_message_budget")
    item = {"chain_index": 0, "type": kind, "message": message,
            "message_bytes": size, "message_truncated": clipped}
    if code:
        item["code"] = code
    return item


def _path_location(reported: str) -> tuple[str | None, str]:
    """Classify a location without filesystem or URL access."""
    lowered = reported.lower()
    if lowered.startswith("node:") or reported in ("<anonymous>", "native"):
        return None, "runtime_internal"
    if lowered.startswith(("http:", "https:")):
        return None, "remote_url"
    if lowered.startswith("file:"):
        try:
            if any(ord(char) < 0x20 or ord(char) == 0x7f for char in reported):
                return None, "invalid_file_url"
            parsed = urlsplit(reported)
            if (parsed.scheme != "file" or parsed.netloc.lower() not in ("", "localhost")
                    or not parsed.path.startswith("/") or parsed.query or parsed.fragment
                    or re.search(r"%(?![0-9A-Fa-f]{2})", parsed.path)):
                return None, "invalid_file_url"
            decoded = unquote(parsed.path, encoding="utf-8", errors="strict")
            if any(ord(char) < 0x20 or ord(char) == 0x7f for char in decoded):
                return None, "invalid_file_url"
            return decoded, "not_checked"
        except (ValueError, UnicodeError):
            return None, "invalid_file_url"
    # A Windows drive is a path claim, not an arbitrary URL. The POSIX source
    # collector will reject it rather than guess a translation to a local path.
    if _SCHEME.match(reported) and not re.match(r"^[A-Za-z]:[\\/]", reported):
        return None, "unsupported_location"
    if "eval at " in reported or reported.startswith("<"):
        return None, "unsupported_location"
    return reported, "not_checked"


def _frame(path: str, line: int, column: int | None, function: str | None,
           number: int, kind: str, cutoffs: set[str]) -> dict:
    path, size, clipped = _clip(path, MAX_PATH_BYTES)
    if clipped:
        cutoffs.add("path_metadata_budget")
        lookup, status = None, "path_metadata_budget"
    else:
        lookup, status = _path_location(path)
    if function is not None:
        function, _, function_clipped = _clip(function, MAX_FUNCTION_BYTES)
        if function_clipped:
            cutoffs.add("function_metadata_budget")
    return {"frame_id": f"F{number}", "chain_index": 0, "reported_path": path,
            "reported_path_bytes": size, "reported_path_truncated": clipped,
            "lookup_path": lookup, "path_status": status,
            "line": line, "column": column, "function": function, "statement": None,
            "path": None, "status": "not_checked", "source_comparison": "unknown",
            "evidence_id": None, "format": kind}


def _v8_location(line: str) -> tuple[str, int, int, str | None] | None:
    match = re.match(r"^\s+at (.+)$", line)
    if not match:
        return None
    location, function = match[1], None
    if "eval at " in location:
        return None
    if location.endswith(")") and " (" in location:
        function, location = location.split(" (", 1)
        location = location[:-1]
        # Nested eval locations have multiple distinct file claims. Do not
        # select the apparent outer path or use a guessed source-map target.
        if "eval at " in location:
            return None
    elif location.startswith("async "):
        function, location = "async", location[6:]
    position = _LOCATION.fullmatch(location)
    if not position:
        return None
    return position["path"], int(position["line"]), int(position["column"]), function


def _node_bindings(lines: list[str], exceptions: list[dict], cutoffs: set[str]) -> tuple[dict, dict, set]:
    """Bind one-level Node inspect arrays without flattening unknown structures.

    Aggregate members are recognized only inside an explicitly framed [errors]
    array belonging to AggregateError. Generic indented Error-looking log text
    cannot acquire an exception identity. Nested/member-property structures are
    deliberately incomplete rather than inheriting an outer error's frames.
    """
    headers: dict[int, int | None] = {}
    bindings: dict[int, int | None] = {}
    blocked_frames: set[int] = set()
    active = None
    active_is_aggregate = False
    scope = None

    def record(index, match, parent=None):
        if len(exceptions) >= MAX_FRAMES:
            cutoffs.add("exception_budget")
            headers[index] = None
            return None
        item = _exception(match["type"], match["message"] or "", cutoffs, code=match["code"])
        if parent is not None:
            item["aggregate_parent_index"] = parent
        headers[index] = len(exceptions)
        exceptions.append(item)
        return headers[index]

    for index, line in enumerate(lines):
        cause = _NODE_CAUSE.fullmatch(line)
        bracket = _NODE_BRACKET_AGGREGATE.fullmatch(line)
        root_match = _NODE_EXCEPTION.fullmatch(cause["header"] if cause else
                                                bracket["header"] if bracket else line)
        if root_match and (scope is None or not line.startswith(" ")):
            if scope is not None:
                cutoffs.add("node_aggregate_format_unsupported")
                scope = None
            active = record(index, root_match)
            active_is_aggregate = root_match["type"] == "AggregateError"
            continue
        property_match = _NODE_ERRORS_PROPERTY.fullmatch(line)
        if property_match:
            if scope is None and active_is_aggregate and property_match["body"] == "[]":
                active = None
                active_is_aggregate = False
                continue
            if scope is not None:
                scope["blocked"] = True
                cutoffs.add("node_aggregate_format_unsupported")
            else:
                valid = active_is_aggregate and property_match["body"] == "["
                scope = {"indent": len(property_match["indent"]), "parent": active, "blocked": not valid}
                if not valid:
                    cutoffs.add("node_aggregate_format_unsupported")
            active = None
            active_is_aggregate = False
            continue
        if scope is not None:
            indentation = len(line) - len(line.lstrip(" "))
            member_indent = scope["indent"] + 2
            if line == " " * scope["indent"] + "]":
                scope = None
                active = None
                continue
            member = _NODE_EXCEPTION.fullmatch(line[member_indent:]) if indentation == member_indent else None
            if member and not scope["blocked"] and not line.endswith(" {"):
                active = record(index, member, scope["parent"])
                continue
            # The comma belongs to Node's inspect array, not the location.
            stack_line = line.removesuffix(",")
            location = _v8_location(stack_line)
            if location is not None:
                bindings[index] = active
                if scope["blocked"] or active is None or indentation < member_indent + 4:
                    blocked_frames.add(index)
                    bindings[index] = None
                    if active is not None:
                        cutoffs.add("node_aggregate_format_unsupported")
                continue
            if not line.strip():
                continue
            # Multiline messages, nested causes/aggregates, primitive members,
            # and unrecognized delimiters must not borrow the previous member.
            scope["blocked"] = True
            active = None
            cutoffs.add("node_aggregate_format_unsupported")
            continue
        # Node appends an inspect-object brace to its final outer stack line
        # when the error has [errors], [cause] or other displayed properties.
        if _v8_location(line.removesuffix(" {")) is not None:
            bindings[index] = active
    if scope is not None:
        cutoffs.add("node_aggregate_format_unsupported")
    return headers, bindings, blocked_frames


def parse_javascript(error_output: str) -> dict:
    """Return bounded location metadata, with explicit V8/diagnostic ordering.

    ``lookup_path`` is the exact path claim or a decoded local file URL; it is
    not an approved path. Skip reads for every non-``not_checked`` path_status.
    Frame caps keep the first locations, because V8 lists the innermost first.
    TypeScript's primary diagnostic and terminal_exception are its first error.
    """
    if not isinstance(error_output, str) or "\x00" in error_output:
        raise Refusal("invalid_error_output")
    try:
        if len(error_output.encode("utf-8")) > MAX_ERROR_BYTES:
            raise Refusal("invalid_error_output")
    except UnicodeEncodeError:
        raise Refusal("invalid_error_output") from None
    lines = re.split(r"\r\n|\r|\n", strip_terminal_controls(error_output))
    frames: list[dict] = []
    exceptions: list[dict] = []
    cutoffs: set[str] = set()
    # Compiler diagnostics have an unmistakable marker and no traceback order.
    # Do not mix an unrelated stack excerpt into this compiler-error report.
    for line in lines:
        match = _TS_POSITIONAL.fullmatch(line) or _TS_PRETTY.fullmatch(line) or _TS_GLOBAL.fullmatch(line)
        if not match:
            continue
        if len(exceptions) >= MAX_FRAMES:
            cutoffs.add("exception_budget")
            if "path" in match.groupdict():
                cutoffs.add("frame_budget")
            continue
        exceptions.append(_exception(match["type"], match["message"], cutoffs))
        if "path" in match.groupdict():
            frame = _frame(match["path"], int(match["line"]), int(match["column"]),
                           None, len(frames) + 1, "typescript", cutoffs)
            frame["exception_index"] = len(exceptions) - 1
            frames.append(frame)
    kind = "typescript" if exceptions else None
    if kind is None:
        exception_indices, bindings, blocked_frames = _node_bindings(lines, exceptions, cutoffs)
        # A syntax/runtime header is printed before its source/caret block. It
        # supplies the project location even when the remaining stack is internal.
        if exception_indices:
            first_error = next(iter(exception_indices))
            for index in range(max(0, first_error - 6), first_error):
                header = _HEADER_LOCATION.fullmatch(lines[index])
                body = lines[index + 1:first_error]
                # V8 omits its caret for an unexpected EOF: the source line,
                # whitespace-only marker line and blank separator still form
                # its normal source block. Keep this exception narrow so an
                # arbitrary path followed by an error does not become a frame.
                first_exception = exceptions[0] if exceptions else None
                eof_block = (first_exception is not None
                             and first_exception["type"] == "SyntaxError"
                             and first_exception["message"] == "Unexpected end of input"
                             and len(body) == 3 and not body[1].strip() and not body[2])
                if (header and (header["path"].startswith(("/", "file:", "node:"))
                                or re.search(r"\.[cm]?[jt]sx?$", header["path"]))
                        and (eof_block or any(re.fullmatch(r"[ \t]*\^+[ \t]*", candidate)
                                             for candidate in body))):
                    frame = _frame(header["path"], int(header["line"]), None, None,
                                   len(frames) + 1, "node", cutoffs)
                    frame["exception_index"] = 0
                    frames.append(frame)
                    break
        for index, line in enumerate(lines):
            if index not in bindings:
                continue
            location = _v8_location(line.removesuffix(",").removesuffix(" {"))
            if len(frames) >= MAX_FRAMES:
                cutoffs.add("frame_budget")
                continue
            frame = _frame(*location, len(frames) + 1, "node", cutoffs)
            frame["exception_index"] = bindings[index]
            if index in blocked_frames:
                frame["path_status"] = "node_aggregate_format_unsupported"
            frames.append(frame)
        # Node prints source/caret headers for runtime errors too. Prefer a
        # same-location stack frame, which additionally supplies its function
        # and column, rather than repeating the header as the primary frame.
        if frames and frames[0]["column"] is None:
            header = frames[0]
            if any(frame["lookup_path"] == header["lookup_path"] and frame["line"] == header["line"]
                   and frame["path_status"] == "not_checked" for frame in frames[1:]):
                frames.pop(0)
                for number, frame in enumerate(frames, 1):
                    frame["frame_id"] = f"F{number}"
        if frames or exceptions:
            kind = "node"
    primary = next((frame["frame_id"] for frame in frames if frame["path_status"] == "not_checked"), None)
    return {"frames": frames, "exceptions": exceptions, "chain_relations": [],
            "cutoffs": sorted(cutoffs), "format": kind,
            "frame_order": "diagnostic_order" if kind == "typescript" else "innermost_first",
            "primary_frame_id": primary,
            "terminal_exception": exceptions[0] if exceptions else None}
