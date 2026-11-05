# Getting ready for an actual local-model trial

This build adds startup diagnostics and a repeatable development-trial runner. It does not install anything on your PC, tune a model automatically, qualify a model for routing, or measure the main assistant's final-answer accuracy.

## Check startup

From the extracted `shake-and-bake` folder on Linux:

```bash
PYTHONPATH=src python3 -B -m shake_bake doctor
```

This checks Python, Linux support, bundled interface files and a point-in-time loopback port probe. It does not open a browser, inspect a project, download a model, change settings or run generation. If the workbench is already running, its occupied port is expected. Use that instance, or pass another `--port` value to both doctor and gui. Passing startup checks is not a visual review.

Optional metadata-only check against a trusted local Ollama daemon:

```bash
PYTHONPATH=src python3 -B -m shake_bake doctor \
  --check-ollama --model qwen3.5:9b-q4_K_M --json
```

Use the exact installed model name. The command checks inventory, local model metadata and a stable reported digest. It sends no source and never calls `/api/chat` or `/api/pull`. Remote metadata is refused. It cannot attest loaded weight bytes or verify the daemon's cloud-disable setting; configure the daemon separately using the linked guidance in README. RAM describes the machine running the command; GPU memory and speed stay unknown rather than inferred from a model name. This environment's report is not a report about Andy's PC.

Start the workbench after checks:

```bash
PYTHONPATH=src python3 -B -m shake_bake gui
```

## Capture the mechanical baseline

```bash
PYTHONPATH=src python3 -B benchmarks/model_trial.py run \
  --evidence-only --output trial-runs/evidence-01
```

All ten known cases are selected by default. `--case boundary` selects a smaller first smoke run. Output must be a new directory outside the benchmark dataset. No previous run is overwritten. The runner records a shuffled, seeded plan; each completed attempt is flushed to `attempts.jsonl`. It saves `trial.json` and a blank `reviews.json` grading sheet. Grading keys remain outside each source fixture and are not sent to the helper.

## Run one installed candidate explicitly

```bash
PYTHONPATH=src python3 -B benchmarks/model_trial.py run \
  --model qwen3.5:9b-q4_K_M --repeat 3 --seed 17 \
  --output trial-runs/qwen-9b-01
```

This is an example candidate, not a download or a recommendation based on local measurements. Test another candidate in a separate directory with the same cases, seed, settings and repeat count. At most three repetitions of ten cases are allowed. Each model request has its existing shared 30-second deadline; a full trial can take several minutes. Keep the daemon trusted and cloud-disabled. No host/cloud client is invoked.

The receipt records helper/pipeline identity, trial/task-runner hashes, manifest/key hashes, source hashes, exact tasks and captured evidence, reported model digest and quantization details when supplied, requested settings, per-attempt time, reported usage, failures and unresolved interpretations. Requested settings are not proof that every server honors them. The first request is not labeled a cold start; load state remains uncontrolled, while reported load duration is retained when available. GPU throughput is not fabricated.

Model identity is checked before and after generation. Drift or remote metadata stops the trial without selecting a substitute. Changed fixtures, benchmark inputs or helper pipeline stop further attempts. Timeouts, truncation and context-budget refusals remain failed attempts; caps are not quietly widened. FINISHED or exit 0 means collection finished, not that the model passed. Inspect `failed_attempt_count` and review the statements.

A timeout or transport failure also stops further requests: disconnecting the client does not prove that Ollama stopped its GPU work. Check the trusted daemon before starting another run. The stopped trial keeps its failed attempt and cannot produce a full reviewed score.

## Review correctness separately

Read each saved handoff against `benchmarks/task-lab/grading-keys.json` and the captured source. In `reviews.json`, enter a reviewer name and fill every attempt:

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
  --trial trial-runs/qwen-9b-01/trial.json \
  --reviews trial-runs/qwen-9b-01/reviews.json
```

The grading sheet is bound to the exact receipt hash. Missing fields, duplicate attempts, mismatched receipts and inconsistent passes cannot produce a reviewed score. A partial or interrupted run leaves accuracy unset. Once fully reviewed, failed attempts count against accuracy rather than disappearing from the denominator. Reviewer identity and judgments are self-asserted owner records, not authenticated independent assessment. Evidence-only review is not a semantic model score.

Usage sums cover only validated worker responses that supplied usage. Missing or rejected-response usage remains unknown and can include real failed work. Full-task cloud usage and savings remain unknown. Repetitions expose variation but are not additional independent cases.

## Recovery and next gate

Ctrl+C normally saves an INTERRUPTED receipt plus completed checkpoints. A hard kill or power loss can leave only `plan.json` and complete lines of `attempts.jsonl`; the last line can be incomplete. There is no automatic resume or reconstructed pass. Preserve that directory and start a new uniquely named run. These checkpoints are separate from the workbench's session-only job history.

The ten exposed cases remain development material and cannot promote a model automatically. Routing qualification still needs unseen cases, reviewed outcomes, a paired native-host baseline, matching identities, no critical regression, and measured performance on the owner's hardware. Browser visual review, real inference, host integration and savings remain distinct gates.

## Version 0.4.0.dev6 observations and limits

Doctor and Model details now expose bounded CPU/RAM/container/GPU observations of the environment running the process. Missing GPU memory is not proof of CPU-only hardware. Metadata-only model checks verify reported digest/runtime stability and expose quantization/context/capabilities. Trial receipts retain that runtime and exact shared request settings (`think: false`, `keep_alive: 0`, non-streaming); a runtime change stops further attempts. No context, memory-fit or accuracy claim follows from metadata.

Two complete ten-case Qwen development runs found reasoning errors despite valid structured output. See validation-0.4.0.dev6.md before interpreting a successful run as a useful model handoff. The semantic review sheets remain pending; exposed repetitions do not promote routing profiles.
