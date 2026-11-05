# Per-PC model calibration

Status: explicit capability/model metadata checks and per-call runtime stability are implemented in 0.4.0.dev6. Automatic tuning, persisted installation profiles and full hardware-aware policy enforcement remain planned. See validation-0.4.0.dev6.md.

Every installation needs a local performance/accuracy profile. A published model ranking can shortlist candidates, but cannot select a proven winner for a particular computer, quantization, runtime and task. No paid inference or cloud test is required by the local calibration design.

## Proposed first-run flow

| Stage | What the user sees | Required evidence |
| --- | --- | --- |
| Check this computer | A simple capability card; unknown values clearly labeled. | RAM, available memory, CPU, detected GPU/VRAM/backend, OS and runtime. Current doctor reports a subset; GPU details remain unknown. |
| Offer candidates | A small list of local models likely to fit, with download sizes/terms checked before an explicit download choice. | Exact permitted model tags, quantization, memory budget and local metadata. No silent download. |
| Quick accuracy check | Progress through a few known tasks, with exact source and visible failures. | Structured-output validity, evidence coverage, omissions and unsupported claims. No fluency-based confidence score. |
| Tune a few settings | Best accuracy as the default, with measured speed and memory tradeoffs. | Compare bounded context/output budgets and supported thinking settings, changing one factor at a time. Current trial settings are fixed, not an automatic search. |
| Choose by task | A recommended local profile for Code, Troubleshoot, Documents or Search, or an honest unqualified status. | Held-out review and the paired native-host baseline, then speed only among candidates meeting accuracy gates. |
| Save and explain | Expand “Why this model” to see this PC's measurements, settings and limits. | A local profile with model digest, quantization, settings, runtime/hardware identity, evaluation cohort and date. No user account needed in the proposed design. |

## Keep the settings reproducible

The proposed profile binds model digest, quantization, inference backend/runtime, relevant driver versions, task category, context/output/thinking options, helper pipeline identity, and evaluation results. It records cold and warm conditions explicitly and keeps GPU offload, memory headroom and concurrency measurements separate from correctness.

After a material change, retain historical receipts, mark the old profile stale, and re-test before automatic selection. Do not treat a model tag alone as identity. A new PC should run its own trials rather than inherit another PC's performance claims. Existing owner policies currently enforce model/pipeline identity and reviewed cohorts; they do not yet enforce the full proposed hardware/runtime identity.

Calibration must not overfit the ten exposed development cases. Keep tuning material separate from unseen acceptance cases. Repeated runs measure variability, not independent evidence. Use exact evidence and useful unknowns when no model passes. A local benchmark win does not establish that the resulting Claude/ChatGPT final answer improved.

## Bound the first-run work

Offer a clear estimate and stop/cancel control before generation or downloads. Keep concurrency at one for the first profile, allow an explicit memory/time budget, and stop on identity changes, output failures or memory pressure. Do not silently increase limits or select a remote model. Let the user keep the diagnostic evidence path even when no model can be qualified.

Implementation sequence: retain current per-run receipts; add capability detection and a versioned local profile store; enforce hardware/runtime/settings identity in the selector; add a bounded calibration runner; then build the guided first-run UI. Actual model quality, memory fit and calibration time must be measured on real PCs before claiming this experience is complete.
