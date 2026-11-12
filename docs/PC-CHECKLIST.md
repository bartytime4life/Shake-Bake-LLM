# Run on your PC: checklist

Updated November 11, 2026 · guidance for the reviewed `0.4.0.dev37` code

Nothing below is marked complete until it has been checked on your actual PC. The development environment's program tests and recorded preview do not complete these items. Commands run from the extracted `shake-and-bake` folder on Linux.

Use the [prioritized to-do list](../TODO.md) to choose the next item. Start with the evidence-only workflow and actual-PC startup checks. Local-model checks and trials are optional; host integration, unseen accuracy and whole-task savings have separate qualification checks.

The [current status](current-status.md) and [dev37 recovery
record](captured-report-recovery-2026-11-11.md) identify the reviewed build and its
516 Python tests, 134 source/installed browser scenarios, 75 JavaScript checks
and official SDK 2.3.0 checks. These synthetic and isolated-installation checks
do not mark any owner-PC item below complete.

The [November 5 local walkthrough](pc-readiness-2026-11-05.md) records the completed
owner-PC subset, the corrected refresh-completion message and remaining gaps.
This reusable checklist stays unchecked; the linked report identifies the
particular package, browser and machine evidence instead of implying every
installation has passed.

## First: identify the code you are actually running

Use the exact reviewed revision and artifact from [current status](current-status.md)
and its linked acceptance record. The version label alone does not identify
installed bytes. The earlier PR #11 hashes in the November 5 records identify
that historical clipboard build; they are not the expected hashes for dev37.
Use a supported Python 3.11+ interpreter for the commands below; substitute its
explicit path if your default `python3` is older.

- [ ] In the trusted checkout, record `git rev-parse HEAD` and `git status --short`.
  Compare the revision with the reviewed code you intend to run. Checkout
  ancestry alone does not identify an installed wheel or uncommitted changes.
- [ ] Record `sha256sum src/shake_bake/web/app.js` and compare it with the exact
  reviewed revision. For package acceptance, also verify the wheel checksum and
  the code/assets/legal-byte checks in that build's record. One interface hash
  is not a complete package check.
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
- [ ] Choose **Prepare source brief**, enter a question about the selected **Synthetic demo**, then select **Prepare brief**. Review source excerpts and captured request/identity in **Review & export**. No model is needed.
- [ ] In **Diagnose a failed run**, use **Try a labelled example**, then explicitly select **Find failing source**. Confirm its synthetic label, captured source and original error; a source match does not establish a cause or fix.
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

Choose **Prepare source brief**, open **Options**, then **Model details** and
expand **This computer & selected model**. **Check this computer** works with
Local AI off and does not contact Ollama. Turning Local AI on permits explicit
inventory/model metadata checks; it does not itself generate notes. Choose
**Try a candidate — unqualified** to expose the installed-model selector. Do not
prepare a model-assisted task during this walkthrough. An installed model must
be selected by the operator; an actual candidate trial additionally requires
the owner's `gui --allow-candidate-trials` launch option and acknowledgement.

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

## Copy and export recovery

- [ ] Prepare a synthetic brief. Copy must immediately show which job is waiting,
  then retain the browser-reported result or failure. Do not equate a resolved
  Promise with verified paste/readback in every browser.
- [ ] Open **Review & export**, select all text and use the device Copy
  command. Compare the pasted text with this field and the downloaded JSON.
  Decode the original-request JSON string to check whitespace and line endings.
- [ ] If a copy is still pending, another copy must not queue. The displayed brief
  stays selectable/downloadable, and a late result must identify its earlier job
  after the pinned brief changes.
- [ ] Record actual clipboard transfer separately from synthetic Promise tests
  and UI selection. The [November 5 follow-up](copy-and-screening-2026-11-05.md)
  records one exact native/manual in-app transfer plus earlier empty readbacks;
  broader timing, permission and device checks remain open.

The [current evaluation record](evaluation-status.md) includes separately frozen thinking-budget probes. Their diagnostic final-content acceptance is not production acceptance; the standard trial commands below request the shipped thinking-off `handoff_prompt_v1` baseline: 8,192 context tokens, 1,024 output tokens and a 30-second shared deadline. Requested settings do not attest runtime behavior.

## Retained reports and startup recovery

- [ ] After a successful synthetic failed-run check, make a different input and
  perform an unsuccessful check. The earlier report must remain labelled as a
  previous capture. Copy/manual-copy/text export wait while inputs differ or a
  check is pending; **Download captured JSON report** saves the displayed
  capture, including its original inputs, rather than newer unsent edits.
- [ ] Save needed failed-run JSON before a successful replacement, page reload
  or tab closure. This report is held in the open tab; it is not durable history.
- [ ] For source briefs, distinguish failed/denied tasks from prepared or
  incomplete captures in **Recent briefs**. Reload may restore an earlier usable
  capture while retaining a newer task draft, only while that capture remains
  in the service's limited history. Older service metadata can be labelled
  completed and require manual review; it does not imply evidence is prepared.
- [ ] On a slow or failed initial connection, **Preparation mode** stays disabled
  until saved choices are restored. Recovery must preserve task/error inputs
  and must not silently replay a check, preparation, connection approval or
  model request.

The [dev37 recovery record](captured-report-recovery-2026-11-11.md) covers these
cases with synthetic fixtures and an isolated browser/service walkthrough.
Recheck on this PC before marking them complete; it does not add hard-crash
resume, durable jobs or automatic restoration of source-folder approvals.

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
