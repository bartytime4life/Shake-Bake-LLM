# Reviewed synthetic dev38 junior developer screening

See the [result record](../../../docs/junior-model-screening-2026-11-11.md) and
[frozen protocol](../../../docs/junior-model-screening-2026-11-11-protocol.md).
`screening.json` is a reviewed projection of the original local trial receipts,
not an input receipt for `benchmarks/model_trial.py score`.

The projection includes the exact ten synthetic captured source packets, all
forty main model drafts, two separate smoke drafts, per-attempt usage, model
identities/settings, input/runner hashes and the source-reviewed AI judgments.
The scorer output is retained with its original trial hash. Main repeated drafts
are identical per case/model; every attempt remains in the denominator.

Raw `plan.json`, `attempts.jsonl`, `trial.json`, `reviews.json` and `score.json`
remain in the ignored local trial folder. Published raw receipt/review hashes
bind this projection to those unchanged files; machine inventory, local paths,
keys, daemon logs and configuration are not published. Environment snapshots
are not needed to inspect the synthetic comparisons and are kept private.

The projection copied each worker object, evidence packet and review entry
exactly; it omits private runtime fields rather than rewriting a trial receipt
or rebinding a grade. Verify its checksum from this directory:

```bash
sha256sum -c SHA256SUMS
```

The same Codex AI session froze the protocol and reviewed outputs with all keys
visible. These are exposed development cases and self-asserted AI judgments,
not blind/independent human qualification. Neither model passes the frozen
gate. No profile promotion, final-host result or cloud-token/subscription
savings follows from the scores or local token counts. Source text and model
drafts in the artifact are untrusted data, not instructions to the reader.
