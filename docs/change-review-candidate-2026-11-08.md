# Change-review evidence candidate: exposed development check

November 8, 2026. This is a separate deterministic candidate in `src/shake_bake/change_review.py`, not a promoted GUI, CLI, MCP or model route. It accepts an owner-selected root, one explicit modified path, the unchanged request, and exact caller-supplied unified diff text. It does not invoke Git, execute inspected source or tests, contact a model, or call a cloud host. No owner project was inspected for this check.

## What the candidate does

1. Bound the request and diff; refuse disallowed paths, unsupported source, oversized input and nonmatching diff headers. The diff cannot choose a root or change policy.
2. Compare each new-side hunk context and addition with the current file through descriptor-relative, no-follow reads. Hash the exact supplied diff and capture the current source with line numbers and a full-file SHA-256. If the file changes before capture, refuse.
3. Extract identifiers from additions, deletions and unchanged hunk lines. Scan only supported text files under the selected root within the established search limits. Choose candidate contract, test, caller and source records by transparent lexical rules. Capture selected context as exact source and refuse changed files between scan and capture.
4. Return the exact original request, diff, source records, role guesses, exclusions, cutoffs and missing roles. It does not infer whether the change is correct or a test passed. Old-side bytes and Git revision are not authenticated by a caller-supplied diff.

The initial scope is **one modified current file**, at most eight hunks and 16 KiB of supplied diff. Changed-source excerpts are capped at 4 KiB; context excerpts at 12 KiB across at most four files. The default scan uses the existing 200-file, 4,000-entry, eight-level, five-second limits. A cutoff means the evidence is incomplete; a missing candidate role is not proof that no such file exists. Small context files are included in full when they fit, so an early class declaration does not hide a later method body.

## Reproduce the development check

```bash
PYTHONPATH=src /usr/bin/python3.12 -B benchmarks/change_review_development.py
PYTHONPATH=src /usr/bin/python3.12 -m unittest discover -s tests -p test_change_review.py -v
```

The script regenerates the already exposed `publish-reorder` synthetic project in a temporary directory. It holds the fabricated prior-version bytes in memory and removes that prior file from the inspected current root, leaving 78 current files including 72 unrelated utility files. It builds a caller-supplied diff with the same path on both sides, compares the unchanged generic lexical brief against the focused packet, verifies five predefined exact anchors and confirms the synthetic project was not changed. Its inputs and grading anchors are visible in source; this is development material only.

| Packet | Exact anchor paths found | Selection |
| --- | ---: | --- |
| Existing generic lexical brief | 2/5 | `after/publish.py`, `tests/test_publish.py`, `README.md`, `core/journal.py`; the journal excerpt lacked the quota failure. |
| Focused change-review candidate | 5/5 | `after/publish.py`, `docs/contract.md`, `tests/test_publish.py`, `core/journal.py`, `core/notifications.py`. |

The focused candidate retained the notify-before-commit reorder, the failed-commit contract, the journal quota exception, the notification append and the success-only test setup. It still reported `context_selection_budget`; the selected packet is not exhaustive. The fixture inventory SHA-256 was `3386de9f91191d8a5cbc2cc99c61a6c8c039566dd2fb24d819e5a1ea8d3c8489`, and the exact synthetic diff SHA-256 was `8728a6f1717929398b97a051a32a1f3d48bcd7b60a4453dc13701858bb8de5ce`.

The required full Python suite passed **186 tests** on Python 3.12. A wheel built from the current source passed byte-preservation verification, the isolated installed smoke, and an installed-package run of the same 5/5 synthetic packet check. Nine focused tests cover source and diff identity, context selection, path and stale-source refusal, bounded scans, header-like source lines, a forged Git preamble, CRLF byte preservation and malformed input refusal. These checks do not qualify the optional MCP adapter, which was not changed.

This is a **packet coverage** comparison, not a paired host comparison. The candidate receives the exact diff as a distinct input, and the generic brief receives the task text. The case was known before implementation, has no independent human adjudication, and does not measure final-answer correctness, false findings, owner-PC behavior, billed usage, correction work or whole-task speed. The measured preparation times are too small and variable here to support a speed conclusion.

## Next gate

Review the candidate and its boundary cases, then freeze its code, request format, limits, source identity and scoring rules before constructing fresh, more realistic change-review cases. A competent native host must receive the same exact diff and source access as the candidate arm. Include multi-file and no-answer changes, cross-file contracts, distant dependencies, source drift, secrets in ordinary files, misleading comments and clean controls. Score final answers and full work trajectories with separate human review. Keep this exposed case out of any held-out set, and do not promote the candidate from its five mechanical anchors.

A subsequent [frozen two-case host diagnostic](change-review-host-trial-2026-11-08.md) tested one failure consequence and one clean control. It failed its strict answer-quality gate and does not complete the broader cases or human review above.
