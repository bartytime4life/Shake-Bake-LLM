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


def scan(text: str) -> list[tuple[str, int, str]]:
    """(kind, 1-based line within text, masked preview) for each credential-looking match."""
    found = []
    for kind, pattern in PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(1) if match.groups() else match.group(0)
            if kind == "password or secret literal" and PLACEHOLDER.match(value):
                continue
            found.append((kind, text.count("\n", 0, match.start()) + 1, "BEGIN … PRIVATE KEY" if kind == "private key" else _mask(value)))
    return found


def screen(search) -> list[dict]:
    """Findings over everything the brief can share, in brief order, at most MAX_FINDINGS.
    Each: kind, where (request, evidence id, map or line index), path, line, masked preview."""
    findings = []

    def add(where, path, base_line, text):
        for kind, line, preview in scan(text):
            findings.append({"kind": kind, "where": where, "path": path,
                             "line": None if base_line is None else base_line + line - 1, "preview": preview})

    add("request", None, None, search.original_request)
    if search.packet is not None:
        for number, record in enumerate(search.packet.evidence, 1):
            add(f"E{number}", record.path, record.start_line, record.text)
    for item in search.context_map:
        add("map first line", item["path"], None, item.get("first_line") or "")
    for entry in search.line_index:
        for item in entry["entries"]:
            add("line index", entry["path"], item["line"], item.get("text") or "")
    return findings[:MAX_FINDINGS]


def warning_lines(findings) -> list[str]:
    """Plain lines for the person sharing the brief; never part of the brief itself."""
    if not findings:
        return []
    lines = [f"Possible credentials in what this brief would share ({len(findings)} found). "
             "Exact text is unchanged; remove or rotate before sharing if they are real:"]
    for item in findings:
        place = item["where"] + (f" {item['path']}" if item["path"] else "") + (f" line {item['line']}" if item["line"] else "")
        lines.append(f"- {item['kind']} in {place}: {item['preview']}")
    return lines
