"""Warn-only screening for credentials in what a brief would share.

The brief is meant to be pasted into a cloud assistant. This pass looks for
high-confidence credential formats in the request, the excerpts, the map's
first lines and the line index, and reports where they are. It never removes
or rewrites anything: exact source stays exact, and the user decides. A
finding carries a masked preview, never the matched secret itself. No match
is not proof that nothing private is present.
"""

import re

MAX_FINDINGS = 20

# (kind, pattern). Formats with a distinctive prefix or structure only, so that
# ordinary code rarely matches; generic high-entropy detection is deliberately absent.
PATTERNS = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?-----")),
    ("AWS access key ID", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})\b")),
    ("GitLab token", re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Stripe live key", re.compile(r"\b(?:sk|rk)_live_[0-9A-Za-z]{16,}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI API key", re.compile(r"\bsk-(?!ant-)(?:proj-|svcacct-)?[A-Za-z0-9_\-]{32,}")),
    ("JSON web token", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("password or secret literal", re.compile(
        r"""(?i)(?<![A-Za-z0-9])(?:[A-Za-z0-9]+_)*(?:password|passwd|pwd|secret|api_?key|access_?token|auth_?token|client_?secret)\b["']?\s*[:=]\s*["']([^"'\s]{8,})["']""")),
)
# Values that are visibly placeholders, not credentials.
PLACEHOLDER = re.compile(r"(?i)^(?:x{4,}|\*{4,}|change[_\-]?me|placeholder|password\d*|secret\d*|(?:example|your|dummy|test|fake|sample)[\w\-.]*|<[^>]*>|\$\{[^}]*\}|\{\{[^}]*\}\})$")


def _mask(value: str) -> str:
    return value[:4] + "…" + f" ({len(value)} characters)"


def _scan(text: str):
    """Yield masked matches so bounded consumers can stop before building a list."""
    for kind, pattern in PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(1) if match.groups() else match.group(0)
            if kind == "password or secret literal" and PLACEHOLDER.match(value):
                continue
            yield (kind, text.count("\n", 0, match.start()) + 1,
                   "BEGIN … PRIVATE KEY" if kind == "private key" else _mask(value))


def scan(text: str) -> list[tuple[str, int, str]]:
    """(kind, 1-based line within text, masked preview) for each credential-looking match."""
    return list(_scan(text))


def screen_failure(report) -> list[dict]:
    """Warn over a failure handoff without changing its exact captured content.

    Uses the source-brief finding schema and patterns. Output is capped while
    scanning, including when a log contains many matches. Line normalization
    applies only to the derived scan copy, following the captured format's
    physical source-line rules; the report itself is never rewritten.
    """
    findings = []
    javascript = report.get("format") in ("node", "typescript")

    def add(where, path, base_line, text, *, source_lines=False):
        if not isinstance(text, str) or len(findings) >= MAX_FINDINGS:
            return
        derived = text.replace("\r\n", "\n").replace("\r", "\n")
        if source_lines and javascript:
            derived = derived.replace("\u2028", "\n").replace("\u2029", "\n")
        for kind, line, preview in _scan(derived):
            findings.append({"kind": kind, "where": where, "path": path,
                             "line": None if base_line is None else base_line + line - 1,
                             "preview": preview})
            if len(findings) >= MAX_FINDINGS:
                break

    project = report.get("project")
    if isinstance(project, dict):
        for key, where in (("id", "project id"), ("label", "project name"), ("path", "project folder")):
            # Do not repeat a possibly credential-containing project value in
            # a finding's location field. Its masked preview identifies it.
            add(where, None, None, project.get(key))
    add("recorded command", None, 1, report.get("command"))
    add("original error output", None, 1, report.get("error_output"))
    for number, record in enumerate(report.get("evidence") or [], 1):
        if len(findings) >= MAX_FINDINGS:
            break
        add(record.get("evidence_id") or f"E{number}", record.get("path"), record.get("start_line"),
            record.get("text"), source_lines=True)
    return findings


def screen_items(items) -> list[dict]:
    """Findings over (where, path, first line number or None, text) items, in order, at most MAX_FINDINGS.
    Each: kind, where, path, line, masked preview."""
    findings = []
    for where, path, base_line, text in items:
        for kind, line, preview in scan(text or ""):
            findings.append({"kind": kind, "where": where, "path": path,
                             "line": None if base_line is None else base_line + line - 1, "preview": preview})
    return findings[:MAX_FINDINGS]


def screen(search) -> list[dict]:
    """Everything a brief can share: the request, excerpts, map first lines and the line index."""
    items = [("request", None, None, search.original_request)]
    if search.packet is not None:
        items += [(f"E{number}", record.path, record.start_line, record.text) for number, record in enumerate(search.packet.evidence, 1)]
    items += [("map first line", item["path"], None, item.get("first_line")) for item in search.context_map]
    items += [("line index", entry["path"], item["line"], item.get("text")) for entry in search.line_index for item in entry["entries"]]
    return screen_items(items)


def screen_failure(error_output: str, command: str, evidence) -> list[dict]:
    """Everything a failure report can share: the pasted output (line numbers within it), the command and excerpts."""
    return screen_items([("error output", None, 1, error_output), ("command", None, None, command)]
                        + [(item["evidence_id"], item["path"], item["start_line"], item["text"]) for item in evidence])


def warning_lines(findings, subject: str = "this brief") -> list[str]:
    """Plain lines for the person sharing the brief or report; never part of it."""
    if not findings:
        return []
    lines = [f"Possible credentials in what {subject} would share ({len(findings)} found). "
             "Exact text is unchanged; remove or rotate before sharing if they are real:"]
    for item in findings:
        place = item["where"] + (f" {item['path']}" if item["path"] else "") + (f" line {item['line']}" if item["line"] else "")
        lines.append(f"- {item['kind']} in {place}: {item['preview']}")
    return lines
