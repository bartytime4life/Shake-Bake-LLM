# Whole-line fitting within the source-byte budget

November 11, 2026 · development candidate `0.4.0.dev35`, based on merged main `e007ae0` (PR #67).

The collector previously discarded an entire candidate window when surrounding lines exceeded the remaining excerpt-byte cap. A generated file with a 20,000-character padding line followed by a short matching line produced no packet, despite the match fitting easily. A second fixture showed the same omission after another file had consumed part of the budget. These failures are reproduced in the committed synthetic regressions.

Dev35 can shorten that window to a contiguous range of whole lines around its strongest match. It preserves the original request, exact retained text, current file hash and source-change refusal. Full windows that fit are unchanged. No dependencies or source-access permissions are added.

## Selection algorithm

For a candidate containing at most seven lines, let `c(i)` be the UTF-8 byte count of line i, including its original line ending, and `w(i)` its existing request-term IDF weight. Fix anchor a to the highest-weight matching line, choosing the earliest on ties. Path-only matches use the first line.

If the full window does not fit the remaining budget R, enumerate every contiguous interval `[b, e)` satisfying:

- `b <= a < e`
- `sum(c(i), b <= i < e) <= R`

Choose the interval with greatest matching-line weight; break ties by more context lines, better balance around the anchor, then earlier start. There are at most sixteen anchored ranges in a seven-line window. Byte prefix sums test the cap exactly; summation uses the same stable IDF-weight arithmetic as coverage selection.

The anchor is mandatory. If that line itself cannot fit, the candidate is still omitted; a weaker match cannot silently replace it. Text is never cut inside a line, and source ranges are never joined across a gap. The final range and identifiers are updated before context collection, capture, source-hash comparison and screening.

This is local fitting inside an already selected candidate. It does not optimize allocation across files or choose a different second region when that region cannot fit. Earlier candidates can still consume the remaining budget. The scan, file-count, read-boundary and record limits remain unchanged. Optional embedding reranking still scores its candidate copies before final byte fitting; the excerpt-byte cap does not limit what that explicitly enabled scorer sees within the approved scan.

## Visible evidence and missing context

The receipt retains `excerpt_budget` and adds `excerpt_window_shortened` only when a shorter range is actually captured. Selected excerpt bytes reflect the exact retained text. Matching lines removed by fitting remain eligible for the existing bounded line index; this is not a guarantee that every omitted line is indexed.

The workbench displays a collection warning, and both copied layouts and CLI layouts state:

> Some excerpts were shortened to fit the source-byte limit. Only whole source lines are included; ask for surrounding lines if needed.

JSON exports retain the exact request, evidence ranges, text, file/excerpt hashes and cutoff records. The warning clears when a later pinned result has no shortening cutoff. Receiving assistants still need surrounding source when the captured range is insufficient; a fitted match is not a diagnosis or proof of completeness.

## Validation

Eight new Python regressions cover a large neighbor, remaining global budget, exact UTF-8/CRLF byte counts, oversized-anchor refusal, unchanged fitting windows, late source-change refusal, both handoff notices and a 200-case exhaustive anchored-range oracle. Four regression methods failed on the pre-change implementation before the fix.

The browser regression creates a disposable project and private state directory, prepares a real source job with Local AI off, verifies the visible warning and both layouts, and reads back the JSON download. It checks lines 2–3, exact Unicode/CRLF content, hashes, request, byte count and cutoffs. It uses no personal browser profile or private project. The test is wired into source and installed-wheel browser CI.

Final local checks:

- All 501 Python tests passed on 3.12 and 3.14, and from a clean installed wheel with PYTHONPATH unset.
- Wheel code, web/demo assets and legal notices matched source bytes. Core runtime dependencies remain empty. The build used setuptools 84.2.1 and wheel 0.48.0.
- All 27 synthetic clipboard/DOM checks passed against source and installed JavaScript; frontend adapter and request-deadline checks also passed.
- The installed Chromium runs passed 14 readiness, 5 clipboard, 42 workbench, 42 failed-run and 12 session-recovery scenarios (115 distinct existing scenarios). The new real byte-fitting/export walkthrough passed against both source and the installed wheel. The extra standalone replay of session recovery is not counted again. Chromium reported 157.0.8103.50.
- The installed demo/shared coordinator and official SDK 2.3.0 stdio subprocess, shared and in-process checks passed with synthetic data and no model/cloud calls. SDK dependencies were installed from the hash-locked requirements.
- Existing retrieval smoke passed 2/2 sources and evidence-only Task Lab passed 10/10 mechanical cases. These are exposed development cases.

The change has not received completed hosted CI or independent human review at the time of these local results. Synthetic mechanical checks do not establish semantic accuracy, whole-task savings, actual-model quality, representative throughput, private-data qualification or owner-PC support. The existing live preview is not changed by this branch.
