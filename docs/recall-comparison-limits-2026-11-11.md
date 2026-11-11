# Recall comparison accepts current collector limits

November 11, 2026 · benchmark-only follow-up to merged main `7f4aaa0` (PR #68). The application package remains `0.4.0.dev35`.

The recall producer and comparer had drifted apart. `SearchLimits` defaults to 20,000 directory entries and supports up to 5,000 files / 100,000 entries. The comparer still allowed only 1,000 files / 10,000 entries. A real synthetic producer receipt using default CLI options therefore failed comparison with `invalid_receipt_limits`, even when compared with itself as a positive control.

The comparer now accepts the same file/entry ceilings as the current collector. It remains a standalone standard-library script that reads receipts only; it does not import the collector, inspect a case repository, collect source, download data or invoke a model. An adjacent comment records the compatibility requirement, and regressions exercise actual producer output rather than only fabricated receipt dictionaries.

## Preserved checks

Both receipts must still have the same case-file, selection and root-location hashes; adapter identity; runtime/platform/timing declarations; rerank configuration; and all six budgets. Unsupported values above the current ceilings are still rejected. Source/selection provenance, per-case hit/recall consistency, duplicate-ID refusal, explicit one-sided refusals and non-overwriting outputs are unchanged.

No scoring equation, macro/micro aggregation, win/tie/loss calculation or timing summary changed. Accepting declared limits is not evidence that a corpus is immutable, that the source hashes attest loaded code, or that a collected answer is correct.

## Validation

Four new regressions cover:

- A current-default receipt produced from a disposable synthetic repository and read through the comparison CLI, preserving its input bytes and receipt-hash binding.
- Actual producer output at the supported 5,000-file / 100,000-entry ceilings, using a one-file fixture rather than a large scan.
- Refusal above each supported ceiling.
- Refusal of unequal budgets even when both expanded profiles are individually supported.

Three of these tests failed against the previous comparer before the fix; the above-ceiling refusal already passed and remains intact.

All 505 tests passed on Python 3.12 and 3.14 and against the unchanged installed dev35 application with PYTHONPATH unset. The comparison CLI positive control runs in a separate Python process with isolated-mode flags. The application package is unchanged, so no new wheel was built and no browser/SDK suites were repeated for this benchmark-only patch. No package, browser code, SDK interface, runtime policy or live preview is changed.

Four retained comparisons were replayed from their existing receipt bytes with the new comparer: default and expanded profiles for `independent-2026-11-07` (nine paired cases each) and `frozen-dev20-2026-11-08` (twelve each). All reported metrics and scan summaries matched the retained comparison reports. Input and retained-report bytes were unchanged. No inspected repositories were accessed for these accounting replays, and the cases remain exposed historical development material, not new held-out results.

The external-recall guide now distinguishes today's 1,000-file / 20,000-entry defaults from its historical pinned 200-file / 4,000-entry recipe. Historical receipts and their exact budgets remain unchanged.
