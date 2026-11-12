# Getting ready for an actual local-model trial

Updated November 11, 2026 for the reviewed `0.4.0.dev37` code. Read [current
status](current-status.md) for revision, hosted-check and installation states,
and [evaluation status](evaluation-status.md) for dated owner-PC/model outcomes.
The standard trial commands request the shipped thinking-off
`handoff_prompt_v1` baseline: 8,192 context tokens, 1,024 output tokens,
temperature 0 and a shared 30-second deadline. Separately frozen thinking-budget
diagnostics do not add CLI settings or qualify a profile.

Startup diagnostics and the repeatable development-trial runner are available.
They do not install anything on your PC, tune a model automatically, qualify a
model for routing, or measure the main assistant's final-answer accuracy. The
[dev37 verification record](captured-report-recovery-2026-11-11.md) reports 516
Python tests, 134 source/installed browser scenarios, 75 JavaScript checks and
official SDK 2.3.0 checks. These mechanical checks add no actual model trial or
new owner-PC qualification.

## Check startup

From the trusted project root on Linux, using Python 3.11 or newer (substitute
an explicit interpreter path if your default `python3` is older):

```bash
PYTHONPATH=src python3 -B -m shake_bake doctor
```

This checks Python, Linux support, bundled interface files and a point-in-time loopback port probe. It does not open a browser, inspect a project, download a model, change settings or run generation. If the workbench is already running, its occupied port is expected. Use that instance, or pass another `--port` value to both doctor and gui. Passing startup checks is not a visual review.

Optional metadata-only check against a trusted local Ollama daemon:

```bash
PYTHONPATH=src python3 -B -m shake_bake doctor \
  --check-ollama --model YOUR_INSTALLED_MODEL --json
```

Use the exact installed model name. The command checks inventory, local model metadata and a stable reported digest. It sends no source and never calls `/api/chat` or `/api/pull`. Remote metadata is refused. It cannot attest loaded weight bytes or verify the daemon's cloud-disable setting; configure the daemon separately using the linked guidance in README. RAM describes the machine running the command. GPU memory is reported only when detected; missing memory and throughput remain unknown rather than inferred from a model name. A report describes only the machine and runtime that actually produced it; identify that environment in its receipt.

Start the workbench after checks:

```bash
PYTHONPATH=src python3 -B -m shake_bake gui
```

The workbench starts with Local AI off on a new installation and retains its
saved service choice on later starts. A source brief works without a model;
failed-run source checks never call one. In the source workflow, open **Options**
and **Model details** for explicit metadata checks. **Check this computer** works
with Local AI off; model inventory/metadata require it on. Preparation mode
waits for the initial session/saved-choice restore and is disabled during an
unconfirmed setting change or disconnection. Existing candidate name/digest
choices remain pinned when refreshing inventory; old facts clear before a
fresh check. These are availability checks, not measured memory fit or accuracy.

The GUI additionally requires `--allow-candidate-trials` at launch and the
operator's acknowledgement before preparing with an explicitly selected
unqualified candidate. This flag does not affect the explicit benchmark command
below or qualify a model. It is unnecessary for evidence-only work.

## Capture the mechanical baseline

```bash
PYTHONPATH=src python3 -B benchmarks/model_trial.py run \
  --evidence-only --output trial-runs/evidence-01
```

All ten bundled known cases are selected by default. `--case boundary` selects a smaller first smoke run. Output must be a new directory outside the benchmark dataset. No previous run is overwritten. The runner records a shuffled, seeded plan; each completed attempt is flushed to `attempts.jsonl`. It saves `trial.json` and a blank `reviews.json` grading sheet. Grading keys remain outside each source fixture and are not sent to the helper. These benchmark scripts run from the trusted source checkout; they are not an installed-wheel command.

`--case` may be repeated for explicit case IDs. `--repeat` accepts 1–3 and
`--seed` records the deterministic ordering seed. An owner-selected
`--dataset /absolute/dataset` uses the [external dataset
contract](held-out-evaluation.md); its declared split is not proof that cases
are unseen or independently authored. Use the matching grading keys and keep
them outside worker-readable fixture roots. Compare only identical
cases/settings/identities across arms.

## Run one installed candidate explicitly

```bash
PYTHONPATH=src python3 -B benchmarks/model_trial.py run \
  --model YOUR_INSTALLED_MODEL --repeat 3 --seed 17 \
  --output trial-runs/candidate-01
```

Replace `YOUR_INSTALLED_MODEL` with the exact permitted installed name. This is
an explicit inference request, not a download or model recommendation. Test
another candidate in a separate directory with the same cases, seed, settings
and repeat count. The bundled ten cases allow up to three repetitions each;
external datasets can contain more cases under their separate bounded
contract. Each model request has the shared 30-second deadline; a full trial
can take several minutes. Keep the daemon trusted and cloud-disabled. No
host/cloud client is invoked.

The receipt records helper/pipeline identity, trial/task-runner hashes, manifest/key hashes, source hashes, exact tasks and captured evidence, reported model digest and quantization details when supplied, requested settings, per-attempt time, reported usage, failures and unresolved interpretations. Requested settings are not proof that every server honors them. The first request is not labeled a cold start; load state remains uncontrolled, while reported load duration is retained when available. GPU throughput is not fabricated.

Model identity is checked before and after generation. Drift or remote metadata stops the trial without selecting a substitute. Changed fixtures, benchmark inputs or helper pipeline stop further attempts. Timeouts, truncation and context-budget refusals remain failed attempts; caps are not quietly widened. FINISHED or exit 0 means collection finished, not that the model passed. Inspect `failed_attempt_count` and review the statements.

A timeout or transport failure also stops further requests: disconnecting the client does not prove that Ollama stopped its GPU work. Check the trusted daemon before starting another run. The stopped trial keeps its failed attempt and cannot produce a full reviewed score.

## Review correctness separately

Read each saved handoff against `benchmarks/task-lab/grading-keys.json` (or the
exact external dataset's keys) and the captured source. In `reviews.json`, enter
a reviewer name and fill every attempt:

| Field | Meaning |
| --- | --- |
| `supported_handoff` | The handoff is accurate, useful and appropriately bounded for this task. |
| `critical_misses` | Required critical findings omitted or contradicted. |
| `unsupported_claims` | Claims not supported by available evidence, including noncritical claims. |
| `unsupported_critical_claims` | The critical subset of unsupported claims. |
| `useful_abstention` | The response usefully identifies a necessary unknown; false when not applicable. |
| `notes` | Evidence for the grading decision, including source references and limits. |

```bash
PYTHONPATH=src python3 -B benchmarks/model_trial.py score \
  --trial trial-runs/candidate-01/trial.json \
  --reviews trial-runs/candidate-01/reviews.json
```

The grading sheet is bound to the exact receipt hash. Missing fields, duplicate attempts, mismatched receipts and inconsistent passes cannot produce a reviewed score. A partial or interrupted run leaves accuracy unset. Once fully reviewed, failed attempts count against accuracy rather than disappearing from the denominator. Reviewer identity and judgments are self-asserted owner records, not authenticated independent assessment. Evidence-only review is not a semantic model score.

Usage sums cover only validated worker responses that supplied usage. Missing or rejected-response usage remains unknown and can include real failed work. Full-task cloud usage and savings remain unknown. Repetitions expose variation but are not additional independent cases.

## Recovery and next gate

Ctrl+C normally saves an INTERRUPTED receipt plus completed checkpoints. A hard kill or power loss can leave only `plan.json` and complete lines of `attempts.jsonl`; the last line can be incomplete. There is no automatic resume or reconstructed pass. Preserve that directory and start a new uniquely named run. These checkpoints are separate from the workbench's session-only job history.

The ten exposed cases remain development material and cannot promote a model automatically. Routing qualification still needs unseen cases, reviewed outcomes, a paired native-host baseline, matching identities, no critical regression, and measured performance on the owner's hardware. Browser visual review, real inference, host integration and savings remain distinct gates.

## Historical dev6 observations and later retained evidence

Doctor and Model details gained bounded CPU/RAM/container/GPU observations in
dev6. These remain observations of the environment running the process. Missing
GPU memory is not proof of CPU-only hardware. Metadata-only model checks verify
reported digest/runtime stability and expose quantization/context/capabilities.
Trial receipts retain runtime and exact shared request settings (`think: false`,
`keep_alive: 0`, non-streaming); a runtime change stops further attempts. No
memory-fit or accuracy claim follows from metadata.

The [dev6 note](validation-0.4.0.dev6.md) recorded two complete ten-case Qwen
development runs with reasoning errors despite valid structured output. Their
original output/review folders are unavailable and remain unscored; subsequent
trials do not reconstruct those runs. Exposed repetitions do not promote routing
profiles.

The later retained owner-PC records are separate: [November 5 screening](screening-2026-11-05.md) retains a timed-out Qwen 3.5 4B run and a completed Qwen 3 1.7B run with an unblinded assistant review of every note. Only four of ten handoffs met the disclosed rubric; no model was promoted. The missing original runs stay unscored. Keep a checksummed review packet outside an expendable checkout, including exact receipts/checkpoints, review sheets and matching inputs. The documented `trial-runs/` output directory is ignored by Git; do not publish raw owner records accidentally.
