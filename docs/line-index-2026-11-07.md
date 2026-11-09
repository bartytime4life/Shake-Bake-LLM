# Matched-line index for lines the excerpts do not cover

Status: development change in `0.4.0.dev15`, November 7, 2026. This is
candidate C1 from the [November 6 web research](research-2026-11-06.md),
aimed at the second cost driver the [host context cost analysis](host-context-cost-2026-11-06.md)
measured: broad reads of large files. On the log comparison fixture the brief
carried one seven-line window from an 1,808-line log, so a host still searched
the file for the second failure. The brief now lists the request-term matches
that no excerpt covers, as line numbers with a short text, so the host can ask
for a range instead of reading or grepping the file. No model or host was run.

## What changed

After primary selection and the controlling-context pass, `search.prepare`
walks the matching files in score order and, for each file with matching
lines that no selected excerpt covers, records up to twelve of them (highest
term weight first, then listed in line order) as `{"line", "text"}` with the
text stripped and cut at 120 characters, together with the file's total and
matching line counts and whether the file was excerpted at all. Bounds: six
files, twelve lines per file, 2,048 bytes in total, each reported as
`line_index_budget` when reached. Files set aside as `low_signal_match` are
not indexed. The texts are untrusted repository strings and are rendered as
inline code with a safe backtick run in both the CLI brief
("## Other matching lines, not excerpted") and the workbench handoff, after
the file map. The worker's collection record does not carry the index, to
keep its source message inside its byte cap; the host does.

## Measured on the four exposed comparison fixtures

| Case | Brief bytes `dev14` → `dev15` | Index content |
| --- | ---: | --- |
| dispatch-path | 3,469 → 4,008 | `app/settings.py` line 1, `DEFAULT_BACKEND = 'local'` |
| publish-reorder | 3,697 → 4,611 | three import lines of `tests/test_publish.py`; `class Journal:`; `docs/contract.md` line 2, the notification contract sentence that was previously only mapped |
| two-log-failures | 3,162 → 3,734 | `logs/ci.txt` line 1805, `FAILED tests/test_deadline.py::test_millisecond_deadline`, the second failure the excerpts missed |
| deployment-unknowns | 2,861 → 3,465 | `receipts/readiness.json` line 2, `"model_inventory": "NOT_COLLECTED"`, previously only mapped |

Two of the four grading keys' required findings that the brief did not carry
before are now present as lines: the second failing test, and the contract
sentence. Two index entries are low value (import lines, a class header) and
cost about 150 bytes. Task Lab keeps 10/10 required spans.

## Self-commit recall is unchanged, by construction

On the twelve self-commit cases the file-level recall with the index equals
recall with the map (38.3%), because the index can only list lines of files
the scan already matched; it raises coverage inside those files, not the set
of files reached. The adapter reports `recall_with_index` separately so the
distinction stays visible.

## Program checks

204 Python tests pass, two new: a 1,802-line synthetic log whose second
failure lands in the index with its line number and text while the first is
excerpted, and a bounds test that caps lines and bytes, reports the cutoff and
skips distractor-excluded files. The clipboard suite renders a fixture index
with an empty line, a not-excerpted file and a crafted text inside inline code.
Both real-Chrome suites pass.

## What this does not establish

- Fewer host turns; that remains the hypothesis for the paired host comparison.
- That twelve lines or 2,048 bytes are the right bounds; they were chosen to
  keep the largest fixture brief under about 1,200 tokens.
- Any ranking quality beyond term weight; low-value lines (imports) are
  listed when they match.
