# Worker compatibility and a rejected prompt experiment

Reviewed November 5, 2026. The shipped `0.4.0.dev8` change is a pre-source compatibility guard. The experimental preparation prompt was rejected and is **not shipped**. All model profiles remain unqualified.

## Shipped behavior

The worker already requests `think: false`. It now checks the model's declared `thinking.values` after metadata inspection and before constructing/sending its source message. A nonempty supported-values list that excludes boolean `false` produces `worker_thinking_mode_unsupported`. Malformed explicit controls produce `worker_invalid_thinking_metadata`. Boolean `false` is distinct from numeric zero or a string named `false`.

Metadata-only inspection remains available, including for incompatible models. If thinking metadata is omitted/null, the legacy request path remains available with compatibility unknown; the existing response checks still reject returned thinking or tool calls. This is a compatibility decision based on trusted-daemon metadata, not accuracy qualification or weight attestation. The [official Ollama contract](https://docs.ollama.com/capabilities/thinking) documents boolean/named thinking controls and absent metadata.

A refused preparation returns `ABSTAIN`, retains the unchanged original request and exact collected evidence, and does not silently substitute a model or change modes. Choose a candidate whose declared controls include boolean `false` for this worker. The fixed output/context/time limits and saved Local AI choice are unchanged.

## Validation and identities

- 171 source tests pass on Python 3.14 and 171 tests pass against the isolated installed Python 3.12 package. Three new tests cover incompatible/malformed metadata refusing before source transmission, supported/legacy no-thinking requests, and exact-evidence retention after refusal.
- The wheel inventory matches packaged source, assets and all legal notices. Installed shared-coordinator/preference checks and official MCP SDK 2.3.0 stdio subprocess checks pass separately from actual-host qualification.
- The temporary local-only Ollama trial observed an actual `qwen3:4b` refusal before generation. A second probe against real Ollama metadata checked the final installed candidate with a metadata-only request allowlist: only `/api/show` was attempted, the result was `ABSTAIN`, and captured source spans/hashes survived. The allowlist would block any attempted generation before forwarding it. That instrumented probe is not a final-host or GPU cancellation trial.
- Final shipped pipeline: `3beaa7d1618112b9f5b5c76f4aac07eec897ab3b7b6d9a545d3c5c70ae663b09`.
- Final local wheel SHA-256: `6b54c562a421c3922064a5dc2454230351ff8e4b540447ff755fb27e815416a8`. Source and isolated installed pipeline identities match.
- Rejected experimental pipeline: `50c9d488a987bab1ab6ecc945b6e45e04542a946a2d0a3ff02987b77a56fd429`. It used a development `0.4.0.dev8` build before the prompt was reverted. Version alone cannot identify that artifact; its receipt, pipeline and archived experimental source/wheel distinguish it.

These installed checks were rerun after reverting the prompt and rebuilding the final wheel. Hosted CI must be observed against the final revision separately. The earlier actual Codex handoff receipts retain their `.dev7` scope; this slice does not claim a new actual-host trial or close INT-01.

## Prompt experiment and decision

The [earlier exposed review](screening-2026-11-05.md) found six missed decisive conclusions in ten Qwen 3 1.7B handoffs. A generic prompt revision requested three short parts—Answer, Evidence, Limits—direct answers, decisive expressions, concrete condition traces and questions only about absent facts. It contained no case-specific expected answers. It was tuned using known cases, so this was an exposed development experiment throughout.

The same installed `qwen3:1.7b` digest, Ollama `0.35.1`, ten exact tasks, fixture/key hashes, seed/order and request limits were used. All ten new attempts completed and retained required exact evidence. The earlier review rubric was copied before inspecting the new output, but the reviewer was still the same unblinded Codex assistant. The earlier run was not a randomized contemporaneous control. Source/request identity matching does not establish a causal or unseen accuracy claim.

| Assistant review | Prior `.dev7` | Rejected prompt experiment |
| --- | --- | --- |
| Supported handoffs | 4 / 10 | 4 / 10 |
| Decisive finding misses | 6 | 6 |
| Unsupported claims/presuppositions | 4 | 5 |
| Task-critical unsupported claims | 3 | 5 |

The unknown-hardware case regressed: the note asserted that an example model was **not installed**, although the captured source contains no inventory. Change review introduced unsupported strict/lenient labels and a mistaken explanation of the changed rejection. Runtime-mode notes wrongly described the transport as hardcoded to local mode despite its captured remote branch. The distant-contradiction case improved under the disclosed rubric by naming both thresholds; that supported judgment and its overbroad context caveat are explicitly recorded for review. Several notes still deferred visible facts to the host as questions and did not follow the requested three-part structure.

The prompt is therefore reverted. The compatibility guard is retained. A 29.830706-second experiment versus the earlier 56.027109-second run establishes no speed benefit: load/cache state was uncontrolled and correctness did not improve. No model, prompt, native-host benefit or savings qualification follows from these results.

The [sanitized receipt](../examples/receipts/worker-compatibility-and-prompt-trial-2026-11-05.json) retains actual notes, case decisions, the final guard probe, comparison identities and the rejection decision. Private originals are in `.local/trial-runs/2026-11-05-dev8-qwen3-1p7b-01/`; raw daemon logs stay private. A separate checksummed comparison packet preserves baseline/experiment receipts, reviews, inputs and the archived experimental source/wheel, clearly labeled as rejected. Existing records are not overwritten.

Next, screen a stronger eligible candidate or a different preparation task design under the same source and failure boundaries. Do not promote a model by strengthening instructions alone or relabel these known cases as an unseen evaluation.
