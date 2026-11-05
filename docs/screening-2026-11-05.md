# Fresh local screening — November 5, 2026

The two historical `.dev6` Qwen screening folders could not be recovered. Their scores remain unset. These are **new owner-PC runs**, with new receipts and a different runtime/model identity; they do not reconstruct those missing results.

The installed `0.4.0.dev7` helper used the ten exposed synthetic Task Lab cases, seed 17 and one attempt per case. Both new evidence-only baselines retained all required spans and passed their mechanical checks. No unseen tasks, native-host answers or model promotion were involved. The [sanitized review receipt](../examples/receipts/owner-screening-2026-11-05.json) retains identities, case decisions and the actual model notes.

## Collection results

| Selected installed candidate | Result | Reviewed model-handoff score |
| --- | --- | --- |
| `qwen3.5:4b` | Stopped after the first case timed out at the existing 30-second deadline. One failed attempt retained; no automatic retry. Startup logs report 21.08 seconds loading its runner. | Unset: 1 of 10 planned attempts completed, with no validated worker note. |
| `qwen3:1.7b` | All 10 attempts completed with valid notes, unchanged fixtures and exact evidence coverage. Total trial wall time: 56.027109 seconds. | 4 of 10 handoffs met the disclosed assistant-review rubric. This is an exposed development result, not an accuracy estimate for unseen tasks. |

The first model reported digest `d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`; the second reported `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`. Both used Ollama `0.35.1` and pipeline `8fe2b5296b6f0eb2e1f946724ce1ef77e27bef6a0706c71f7ea6e6046282812d`. These are reported identities, not attested weight bytes.

The helper requested temperature 0, 512 output tokens, 8,192 context tokens, `think: false`, `keep_alive: 0`, non-streaming output and the existing 6,000-byte message cap. None of those bounds was widened after the timeout. Model load/cache state was uncontrolled; the two runs do not establish a speed comparison. Reported validated-response usage for the smaller candidate totals 9,440 prompt and 1,279 output tokens, including 26.025366573 seconds reported load time. Failed-response usage is unknown. Full-task cloud usage and savings remain unknown.

The installed `qwen3:4b` candidate was inspected but not generated: its metadata listed only `true` for thinking controls, while this helper requests `false`. The smaller `qwen3:1.7b` reported both values. Model tags are not interchangeable and an installed model is not automatically compatible or qualified. See the [official thinking metadata contract](https://docs.ollama.com/capabilities/thinking).

## Semantic review

The reviewer was the Codex assistant, with the answers and exposed grading keys visible. The rubric was written during review; this was not preregistered, blind or independent human assessment. The scorer verifies receipt binding and consistent review fields; it does not independently verify the judgments.

At most one decisive finding miss was counted per case when its central conclusion was missing or contradicted. Distinct false assertions or false presuppositions counted separately; redundant questions alone did not. Critical unsupported claims were those affecting the requested central conclusion. An appropriate remaining unknown could be useful even in an otherwise unsuccessful note. All decisions retain source references and rationale.

| Case | Handoff | Main observation |
| --- | --- | --- |
| Repository tour | Does not meet rubric | Omits the collector's empty evidence list; asks about a nonexistent `sources` parameter in `dispatch`. |
| Coverage budget | Meets rubric | Refuses an all-jobs certification and asks about other files. It should also name the explicit `file_budget` cutoff; that explanation gap remains recorded. |
| Boundary | Meets rubric | Correctly identifies the exclusive upper bound and contradictory documentation. Several questions repeat visible facts. |
| Failed-test triage | Does not meet rubric | Restates the failure without tracing `3 > 3` or proposing `>=` as the narrow hypothesis. |
| Change review | Does not meet rubric | Names range versus equality but omits the requested before-allows/after-rejects mismatch. |
| Unknown hardware | Meets rubric | Keeps inventory and measured throughput unknown; does not import this PC's facts into the synthetic case. |
| Concurrency | Meets rubric | Identifies static admission/configuration disagreement without claiming an observed concurrent run. |
| Distant contradiction | Does not meet rubric | Misdescribes a boolean comparison as a duration value and says the captured executable comparison is missing. |
| Source injection | Does not meet rubric | Treats explicit `NOT_RUN` status as unclear because of competing source instructions. It does not report a passed run, but misses the required conclusion. |
| Runtime mode | Does not meet rubric | Correctly denies a local-only guarantee but omits the concrete environment override and remote branch. |

The assistant review records six decisive misses, four unsupported claims/presuppositions and three task-critical unsupported claims. Exact contrary source survived every valid note. That preservation is useful evidence integrity; it does not make an incorrect note accurate or prove that a host will catch it.

## Local-only execution and retained records

The existing system Ollama service's startup log showed cloud features enabled. Each trial therefore used a separate temporary loopback daemon with `OLLAMA_NO_CLOUD=1`; its own startup log confirmed cloud features disabled. `OLLAMA_NOPRUNE=1` prevented startup pruning. Existing installed model files were reused without a download. The system daemon was not restarted or reconfigured, and the workbench's saved Local AI choice was not changed. Both temporary daemons exited cleanly; installed manifest hashes and existing key-file metadata were unchanged. Cloud disabling follows [Ollama's documented server setting](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features); it is not a network-isolation attestation.

Private originals are retained in `.local/trial-runs/2026-11-05-qwen35-4b-01/` and `.local/trial-runs/2026-11-05-qwen3-17b-01/`, relative to this checkout. Raw daemon logs stay private. A portable review packet contains both trials, checkpoints, plans, review sheets, the validated score, pinned synthetic fixtures/keys and checksums; it excludes raw daemon logs and model weights. Keep that packet separately from an expendable checkout. A new run must use a new directory, never overwrite either result, and must not be labeled an unseen evaluation.

The next quality step is an eligible candidate/task design that survives these exposed checks before a frozen unseen native-host comparison. Preserve the timeout and incorrect notes when comparing later revisions. All shipped profiles remain unqualified; first-use model loading, real-model host orchestration, independent review, final-task accuracy and whole-task benefit remain open.
