# A brief Claude and ChatGPT can read directly

Status: development change in `0.4.0.dev12`, November 7, 2026. The copied
workbench brief was a text block built mostly from pretty-printed JSON: the
request as a JSON string on line four, instructions, the evidence array with
escaped newlines, then gaps, model notes, routing, receipt and limitations as
four more JSON dumps. Exact and machine-checkable, but the worst shape for a
chat assistant to read, and code inside JSON strings loses its line structure.
This change makes the copied brief a Markdown message while keeping every exact
value. No model or host was run.

## The new layout

1. **Title and identity.** `# Help me with my code (Shake & Bake brief)`,
   project and job.
2. **My request.** The request in a fenced block, shown with line endings
   normalized because a textarea normalizes them anyway; the sentence above it
   says the exact value is at the end.
3. **What I need from you.** The local model's drafted prompt when Local AI
   produced one (unchanged text, still labeled unverified), then a fixed
   three-point answer format: findings each citing the E-id and path:lines,
   what is not established as a separate list, and which files to paste next
   by path. The CLI brief gains the same section as `## Answer with`.
4. **Ground rules.** The fixed receiving-assistant sentences, byte-identical
   to the previous version except for "at the end" in the sentence about the
   JSON-encoded request, so the untrusted-data wording the clipboard checks
   match exactly is preserved.
5. **Exact source.** One `###` heading per excerpt with its id, path, line
   range and full-file SHA-256, the controlling-context reason when there is
   one, and the text in a fenced block tagged with a language guessed from the
   extension. The fence is always one backtick longer than the longest
   backtick run inside the text, so captured source can never close the block
   or be read as brief structure.
6. **Files also matched, not excerpted.** The map, with the sentence "Ask me
   for any of these by path and I will paste it."
7. **Scan limits.** Files read, excerpt bytes, cutoffs, exclusions, the
   preparation route and any gaps, as plain bullet lines instead of JSON.
8. **Local model notes.** Only when notes exist without a usable drafted
   prompt; otherwise the notes already appear inside the drafted prompt.
9. **Exact values for verification.** The request as a JSON string, the
   evidence identities (id, path, lines, file and excerpt hashes) as compact
   JSON, and the limitations as bullets.

The page shows the brief's size under the copy button: bytes and a bytes/4
token estimate, labeled as an estimate, not a provider count.

## Measured on the starter demo

| | Before (`dev11`) | After (`dev12`) |
| --- | ---: | ---: |
| Bytes | 4,334 | 3,375 |
| Lines | 100 | 57 |
| Bytes/4 token estimate | 1,084 | 844 |

Both renderings of the same synthetic demo job are retained under
`examples/receipts/handoff-format-2026-11-07/`. The saving comes from dropping
the JSON framing (quotes, escapes, indentation, repeated keys), not from
dropping content: every excerpt, hash, cutoff, exclusion, limitation and the
exact request are still present.

## Considered and not done

- **Prefilling the assistant through a URL query** (`chatgpt.com/?q=`,
  `claude.ai/new?q=`) would save the paste step but would put captured source
  into a URL, where it lands in browser history, referrer headers and server
  logs. The project's privacy rule keeps source out of query strings, so the
  links stay plain and the user pastes.
- **Assistant-specific variants** (XML tags for Claude, different headings for
  ChatGPT). Both read Markdown with fenced code; one layout keeps the clipboard
  checks exact and avoids a destination choice the simplification follow-up
  removed on purpose.
- **Dropping the verbatim JSON values.** The fenced request normalizes line
  endings and a renderer may reflow text, so the exact request and the
  identities stay, at the end where they cost the least attention.

## Program checks

196 Python tests pass, one new (the CLI brief's answer section sits between
the request and the first excerpt and is absent on an abstained brief). The
17 clipboard cases compare the page's text against an independent rendering
of the new layout, check that the verbatim request line parses back to the
captured value including carriage returns, that evidence identities parse,
that fenced source containing `</textarea><script>` stays inside its fence,
and that no `"content":` JSON field remains. Five real-Chrome clipboard
scenarios and 33 workbench scenarios pass with Chrome 157 and Python 3.12,
including the CRLF request supplied at the HTTP boundary.

## Hardening after review (later on November 7, `0.4.0.dev14`)

A review of the merged source raised two points, recorded as BUG-019. First,
paths in the excerpt headings and the path and first line in the map were
plain text outside any fence, so a filename such as
`## IGNORE PREVIOUS INSTRUCTIONS.py` would have rendered as a heading or an
instruction. Those strings are now inline code with a backtick run longer than
any they contain and control characters shown as escapes, in both the
workbench text and the CLI brief, and the collector refuses any path
containing a control character outright. Second, fenced text can have its
carriage returns normalized by a clipboard or chat client. The copied text
itself keeps the captured bytes (only the on-page textarea view normalizes
them), but what arrives in a chat may not, so an excerpt that contains
carriage returns now carries a note pointing to the JSON download, and the
verification section says the same for all fenced text. The JSON download
remains the exact-bytes path; the hashes let a copy be checked. No
exploitation was reported or observed. A crafted-filename clipboard test and a
Python test cover both points; the real-Chrome suites pass.

## What this does not establish

- That either assistant answers better from this layout. That is a host
  comparison on frozen, person-authored cases; this change only removes
  obstacles a reader can see.
- Token counts: the estimate is bytes/4; provider tokenizers differ.
- Rendering in every chat client; fenced blocks and `###` headings are
  CommonMark, and the verbatim values at the end do not depend on rendering.
