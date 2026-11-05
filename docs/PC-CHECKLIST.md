# Run on your PC: checklist

Updated November 5, 2026 · Shake and Bake 0.4.0.dev8, including PR #8

Nothing below is marked complete until it has been checked on your actual PC. The development environment's program tests and recorded preview do not complete these items. Commands run from the extracted `shake-and-bake` folder on Linux.

Use the [prioritized to-do list](../TODO.md) to choose the next item. Start with actual-PC/model readiness and a reviewed real Ollama trial; host integration, unseen accuracy and whole-task savings have separate qualification checks.

The [November 5 local walkthrough](pc-readiness-2026-11-05.md) records the completed
owner-PC subset, the corrected refresh-completion message and remaining gaps.
This reusable checklist stays unchecked; the linked report identifies the
particular package, browser and machine evidence instead of implying every
installation has passed.

## First: identify the code you are actually running

The readiness correction merged in [PR #8](https://github.com/bartytime4life/Shake-Bake-LLM/pull/8)
at `4ddb4b5274ddd6fb1d47170aba5841d9d7c2e0b0`. The package version is still
`0.4.0.dev8`; the version label alone cannot distinguish an older installation.
Use a supported Python 3.11+ interpreter for the commands below.

- [ ] In the trusted checkout, record `git rev-parse HEAD` and `git status --short`.
  Verify that `git merge-base --is-ancestor 4ddb4b5274ddd6fb1d47170aba5841d9d7c2e0b0 HEAD`
  exits 0. This checks checkout history; it does not identify an installed wheel.
- [ ] Record `sha256sum src/shake_bake/web/app.js`. For the PR #8 interface it is
  `8fabff47c2707f82d1958ef158e5dc73aaca66aead508413caa1cfc359c0d2bf`.
  A later interface change needs a fresh expected hash from its reviewed commit.
- [ ] For an installed wheel, use its own Python with `PYTHONPATH` unset and
  record the actual imported location, version and interface hash:

```bash
env -u PYTHONPATH /absolute/app-env/bin/python -B -c \
  'from pathlib import Path; import hashlib, shake_bake; p=Path(shake_bake.__file__).parent; print("Package:", p); print("Version:", shake_bake.__version__); print("Interface SHA-256:", hashlib.sha256((p/"web/app.js").read_bytes()).hexdigest())'
```

Compare that hash with the reviewed checkout. A match covers this interface file,
not all package bytes, loaded model weights or installation authenticity. Keep
private paths, screenshots and readiness JSON outside Git and inspected source.
Record UTC capture time, command/exit status, checkout SHA, installed version/path
and interface hash with each local acceptance record. Do not overwrite old records.

## First: get the app open

- [ ] Keep this project in its own folder with its own configuration and data.
- [ ] Run `PYTHONPATH=src python3 -B -m shake_bake doctor` and read the startup results. If the port is occupied, check whether the app is already open; otherwise choose another port for both doctor and gui.
- [ ] Run `PYTHONPATH=src python3 -B -m shake_bake gui` and open the loopback address it prints.
- [ ] Submit the bundled demo. Confirm the exact source receipts, evidence map and expandable model explanation work.
- [ ] Check a desktop and narrow phone-width layout: readable text, expanding panels, keyboard focus, reduced motion, copy and JSON download. The offline preview is a recorded demo, not a live connection to your PC.

## Next: verify the local model

- [ ] Start your trusted Ollama service and disable its cloud features using the guidance linked in README. No model downloads happen automatically.
- [ ] Run `PYTHONPATH=src python3 -B -m shake_bake doctor --check-ollama --json`. Choose an actually installed, permitted local model; do not assume a suggested tag is installed.
- [ ] Add `--model YOUR_INSTALLED_MODEL` to that command. Confirm local metadata and the reported digest are accepted. This does not attest loaded weight bytes or prove accuracy.

For an installed wheel, substitute
`env -u PYTHONPATH /absolute/app-env/bin/python -B -m shake_bake doctor`
for the source command. Save the actual JSON and exit status locally. No source,
generation, download or model activation is requested by these checks.

## Then: verify the corrected readiness display

Open Model details and expand **This computer & selected model**. Turning Local AI
on permits the explicit metadata checks; do not start a candidate trial during
this walkthrough. An installed model must be selected by the operator.

- [ ] Refresh models, choose an installed candidate and click Check selected model.
  Record its name, digest, reported quantization/capabilities and check time.
  Keep computer observations separate from Ollama-reported metadata.
- [ ] Click Refresh models again. The previous model facts must clear immediately,
  even when the installed digest is unchanged. Recheck explicitly to display facts.
- [ ] Choose another installed model, or clear the dropdown if only one is present.
  Previous model facts must clear. Choosing the first model again must not restore
  its old result without another explicit check.
- [ ] Turn Local AI off and back on. Previous model facts must remain invalidated;
  the off state must block inventory/model checks.
- [ ] If a model naturally disappears, changes digest or becomes unavailable,
  refresh must clear old facts. A replaced name must keep the old explicit pin
  labeled unavailable until the operator chooses the installed replacement.
  Do not delete/re-tag weights or stop a shared daemon merely to mark this box.
- [ ] Record pending-request replacement/removal, failed inventory and stale
  success/failure behavior as unverified on this PC unless actually observed.
  Deterministic regression and Chromium fixtures already cover those transitions
  with synthetic metadata; their results do not establish real Ollama behavior.

Capture expected/observed behavior and failures with each record. A successful
metadata check leaves memory suitability, throughput and reasoning accuracy
unmeasured. Current exposed Qwen screening has reasoning failures; no model is
promoted by completing this checklist. [PR #8 evidence](readiness-invalidation-2026-11-05.md)
and hosted CI are development evidence, separate from these unchecked PC gates.

## Then: one small trial

- [ ] Run the mechanical baseline: `PYTHONPATH=src python3 -B benchmarks/model_trial.py run --evidence-only --case boundary --output trial-runs/pc-evidence-01`.
- [ ] Run the same case with the installed model: `PYTHONPATH=src python3 -B benchmarks/model_trial.py run --model YOUR_INSTALLED_MODEL --case boundary --output trial-runs/pc-model-01`.
- [ ] Review the actual handoff against captured source and `benchmarks/task-lab/grading-keys.json`; fill every field in `trial-runs/pc-model-01/reviews.json`, including reviewer and evidence notes.
- [ ] Score it with `PYTHONPATH=src python3 -B benchmarks/model_trial.py score --trial trial-runs/pc-model-01/trial.json --reviews trial-runs/pc-model-01/reviews.json`. A finished run is not a correctness pass; incomplete reviews leave accuracy unset.
- [ ] Keep failed attempts and unknown usage in the record. Preserve interrupted folders; use a new output directory for the next run.

## Before automatic model selection

- [ ] Calibrate this PC individually: record its actual hardware/runtime, test models and quantizations that fit, and compare task-specific settings. Save measured results for this machine; re-test after material model/runtime/hardware changes. The [per-PC calibration design](per-pc-calibration.md) is planned work, not an implemented automatic tuner.
- [ ] Qualify the [Your computer & tuning GUI](per-pc-calibration-ui.md) so users can see hardware, test progress, task-specific results, selection reasons and stale-profile warnings. The metadata-only capability subsection ships; the full calibration/tuning screen remains planned.

- [ ] Expand to the full development set, compare candidates with matching cases/settings, and test timeouts, cancellation and source/model changes on the real machine.
- [ ] Create an unseen evaluation set and compare against a well-configured native Claude/ChatGPT baseline. Review final task correctness and critical omissions before speed or tokens.
- [ ] Qualify the actual host connection separately. Installed SDK 2.3.0 and [actual Codex synthetic handoff/cancellation checks](codex-host-handoff.md) passed. Active cancellation used an explicitly stopped owned runner. Disconnect/deadline/restart, local-model orchestration and Claude/consumer ChatGPT checks remain pending; the full gate stays open.
- [ ] Promote only an owner-reviewed profile meeting the held-out baseline and identity gates. The trial runner never promotes a model; all shipped profiles remain unqualified.
- [ ] Measure actual cloud usage and successful-task time before claiming savings. Do not promise subscription-limit improvements from estimated tokens.

## Whole-workflow UX checks

- [ ] Walk through first setup, an inert demo, source selection, preparation, evidence review and assistant handoff using the [UX workflow plan](UX-WORKFLOW.md).
- [ ] Verify a user can distinguish evidence-only, actual model preparation, copied/delivered brief and final-answer-pending states.
- [ ] Verify current request, active job and completed result remain distinct through a new draft, failed/cancelled job, retry and export.
- [ ] Qualify the [shared coordinator](shared-coordinator.md) through the actual SDK and each supported host: SDK, the scoped Codex demo and injected active-runner cancellation/recovery have evidence; disconnect/deadline/restart and other hosts still need actual-client trials.
- [ ] Make missing models, stale profiles, limited evidence and connection errors offer specific next actions.
- [ ] Explain and test draft/history/evidence/settings retention, clearing, expiry and restart behavior.
- [ ] Complete actual desktop/phone/keyboard/reduced-motion walkthroughs and record findings before closing UX-01/UI-01.

## Security and bug release gates

- [ ] Review the app's existing MIT licensing choice against the intended distribution model; MIT permits commercial reuse and resale. Preserve required notices and the separate terms in the licensing guide.
- [ ] Inventory exact shipped dependency/model artifacts and their notices. Keep bundled test fixtures self-contained; do not relabel newly added external material under the app license.
- [ ] Retain model source/digest, quantization, actual license/NOTICE text and review evidence before bundling or offering model downloads. MODEL_LICENSES.json contains upstream observations, not completed artifact clearance.

These project-level gates remain pending until their evidence is recorded; the existing development tests do not complete them automatically. Selected development checks for connection limits and queued-expiry recovery are recorded in Known Issues; real-machine and broader qualification remain pending.

- [ ] Verify that inspected source remains unchanged and cannot trigger execution, arbitrary path reads or model-directed actions through any supported interface.
- [ ] Test permitted secret/private-data handling inside ordinary source files, captured evidence, logs and exports. Filename exclusions alone do not establish complete secret protection.
- [ ] Review dependency/optional-SDK origins and exact versions, update/package integrity and integration behavior before release.
- [ ] Complete an independent review of source, local web, model/daemon and export trust boundaries; track findings and closure evidence.
- [ ] Exercise hostile/malformed input, slow connections, concurrency/load and resource exhaustion; record bounded failure and recovery on real machines.
- [ ] Verify unavailable-model, timeout, cancellation, source/model-change and restart behavior. Do not claim a disconnect stops the daemon's GPU work or that hard-crash resume exists.
- [ ] Test real models against source-injected instructions, critical omissions and unsupported claims on unseen reviewed tasks, with the paired native-host baseline.
- [ ] Keep public/shared-user exposure disabled until a separately designed authorization boundary is qualified. Localhost is not multi-user isolation.
- [ ] Close every known release-blocking data exposure, unauthorized execution, source corruption, gate bypass, critical accuracy regression or required stop/recovery failure for the feature being promoted.
- [ ] For each important fix, record reproduction steps, expected/actual behavior, impact, regression check and relevant verification. Keep minor cosmetic defects visible when deferring them.
- [ ] Review [Known Issues](../KNOWN_ISSUES.md), retain honest pending statuses, choose a private reporting channel before a public release, and document recovery/rollback for that release.

Detailed instructions: [PC readiness and trials](pc-readiness-and-trials.md). Remaining engineering gaps: [open gaps](open-gaps.md). Issue statuses and release rules: [Known Issues](../KNOWN_ISSUES.md).
