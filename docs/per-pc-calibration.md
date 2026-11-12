# Per-PC model calibration

Implementation status refreshed for the reviewed `0.4.0.dev37` source. See [current status](current-status.md) for source, validation and delivery identity, and [the workbench guide](visual-workbench.md) for active controls. Manual thinking-budget experiments and their limits remain in [evaluation status](evaluation-status.md); this documentation refresh adds no model trials, automatic tuning or changed worker settings.

Explicit capability/model metadata checks and per-call runtime stability were introduced in dev6; see the dated [validation](validation-0.4.0.dev6.md). They remain implemented. **Options → Model details → This computer & selected model** offers **Check this computer** and **Check selected model**. The computer check reads bounded local metadata without commands or Ollama; the selected-model check requires Local AI on and sends no source or generation. Unknown VRAM, measured memory fit and task accuracy remain unknown.

Automatic calibration, persisted installation profiles, full hardware/runtime/settings-aware selection and the calibration dashboard below remain planned. Browser model/mode preferences and the service's saved Local AI on/off are not a qualified profile store. Either current job-first workflow works without installing or qualifying a model; failed-run source location does not call one. Session folder connection, actual preparation activity and source-draft save/opt-out/clear are implemented separately from calibration.

The proposed calibration feature needs a local performance/accuracy profile for each tested installation. A published ranking can shortlist research candidates, but cannot establish a winner for a particular computer, quantization, runtime and task. Historical candidate research must be rechecked before a new trial or download; this audit makes no new recommendation. No paid inference or cloud test is required by this local calibration design.

## Proposed first-run flow

| Stage | What the user sees | Required evidence |
| --- | --- | --- |
| Check this computer | Existing explicit metadata check, extended into a future capability card; unknown values clearly labelled. | Current bounded observations cover a subset of RAM/available memory, CPU, detected GPU and runtime facts. Measured fit, full driver/backend identity and unavailable GPU/VRAM values require separate evidence. |
| Offer candidates | A small list of local models likely to fit, with download sizes/terms checked before an explicit download choice. | Exact permitted model tags, quantization, memory budget and local metadata. No silent download. |
| Quick accuracy check | Progress through a few known tasks, with exact source and visible failures. | Structured-output validity, evidence coverage, omissions and unsupported claims. No fluency-based confidence score. |
| Tune a few settings | Best accuracy as the default, with measured speed and memory tradeoffs. | Compare bounded context/output budgets and supported thinking settings, changing one factor at a time. Current trial settings are fixed, not an automatic search. |
| Choose by task | A recommended local profile for Code, Troubleshoot, Documents or Search, or an honest unqualified status. | Held-out review and the paired native-host baseline, then speed only among candidates meeting accuracy gates. |
| Save and explain | Expand “Why this model” to see this PC's measurements, settings and limits. | A local profile with model digest, quantization, settings, runtime/hardware identity, evaluation cohort and date. No user account needed in the proposed design. |

## Keep the settings reproducible

The proposed profile binds model digest, quantization, inference backend/runtime, relevant driver versions, task category, context/output/thinking options, helper pipeline identity, and evaluation results. It records cold and warm conditions explicitly and keeps GPU offload, memory headroom and concurrency measurements separate from correctness.

After a material change, retain historical receipts, mark the old profile stale, and re-test before automatic selection. Do not treat a model tag alone as identity. A new PC should run its own trials rather than inherit another PC's performance claims. Existing owner policies currently enforce model/pipeline identity and reviewed cohorts; they do not yet enforce the full proposed hardware/runtime identity.

Calibration must not overfit exposed development material, including the earlier ten-case cohort. Keep tuning material separate from unseen acceptance cases. Repeated runs measure variability, not independent evidence. Use exact evidence and useful unknowns when no model passes. A local benchmark win does not establish that the resulting Claude/ChatGPT final answer improved.

The normal source collector has up to four primary and six software-selected context records (ten total), subject to byte and scan limits. This is a selection bound, not required-span coverage. [Optional local embedding reranking](embedding-rerank-2026-11-07.md) is already implemented for explicit CLI/benchmark use, off by default and outside the normal GUI. It reorders permitted candidates; it is neither automatic calibration nor a qualified quality improvement.

## Bound the first-run work

The proposed calibration runner must offer explicit bounds and stop/cancel controls before generation or downloads. Any duration estimate needs measured support; actual case/attempt counts must not become an invented progress percentage. Keep concurrency at one for the first profile, allow an explicit memory/time budget, and stop on identity changes, output failures or memory pressure. Do not silently increase limits or select a remote model. The current evidence-only path stays usable when no model qualifies.

Implementation sequence: retain per-run receipts and extend existing capability metadata; add a versioned local profile store; enforce full hardware/runtime/settings identity in the selector; add a bounded calibration runner; then build the guided first-run UI. Automatic cloud Send and its acknowledgement UI are separate proposals, not a calibration fallback. Actual model quality, memory fit and calibration time must be measured on real PCs before claiming this experience is complete.
