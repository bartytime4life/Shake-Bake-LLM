# Workbench and Ollama development validation — November 5, 2026

This candidate builds on imported commit `67ee5c2` (`0.4.0.dev4`), preserving the recovered collector, lexical retrieval, bounded helper, routing policy, shared bridge, exposed Task Lab and original 121 tests. The separate bootstrap work is retained in Git history; its SQLite/configuration/engine API is not mixed into this runtime. The [import provenance](import/2026-11-05.md) still describes the byte-preserved archive at import, not this modified candidate.

## Executed checks

- 127 source tests pass on Python 3.14.4: all original 121 plus six candidate checks. New cases exercise a real child against a synthetic loopback model, required launch permission/acknowledgement, exact source/request preservation, digest change after inference, disabled inventory/trials and thinking-output refusal.
- The isolated installed wheel runs 127 tests on Python 3.11.18 without checkout `PYTHONPATH`. The installed shared-controller demo smoke passes. Wheel inspection compares every packaged code/web/demo file and all three legal files with source bytes, and checks that core runtime dependencies remain empty.
- Official SDK 2.3.0: installed GUI plus actual stdio-adapter subprocess replay passes all five tools, shared job visibility, exact evidence, completed-job cancellation, continued service access after client close and connection-file cleanup. The recovered in-process standalone/shared SDK checks also pass. The first replay exposed absent structured responses; explicit structured-output declarations fixed the adapter. These are SDK/transport checks, not actual Claude/ChatGPT host qualification.
- Both synthetic retrieval variants find expected source; the exposed evidence-only Task Lab retains all required spans in 10/10 mechanical checks. This does not measure semantic model accuracy.
- Node checks interface syntax. Actual Chrome desktop/phone/keyboard interactions and image comparison are recorded in design-qa.md. Copy includes original request and exact source; a real JSON download was read back and matched its pinned native task/evidence. Node is not an app runtime dependency.

A stale local build directory initially carried deleted bootstrap modules into the wheel. That generated directory was archived locally and a clean build passed the exact inventory verifier. CI builds from a fresh checkout. No local environments, private captures, model weights or planning exports are committed.

## Real candidate observation

Only the bundled inert `validator.py` and `readme.md` were submitted. No model was downloaded, daemon started/stopped, host account configured or paid provider called. The trusted existing inventory listed three installed candidates.

On this candidate, `qwen3:4b-instruct-2507-q4_K_M`, reported digest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`, completed one GUI-initiated trial. Its server-reported usage was 697 prompt tokens, zero cached prompt tokens, 197 output tokens, 20.203530696 seconds total duration and 13.267777842 seconds load duration. Exact excerpts totaled 455 bytes. Full receipt/job identity are private local artifacts; cloud usage/savings remain unmeasured.

The note described the comparison and demo limitation, but its questions repeated the central question instead of resolving it. It passed structural/reference checks and remains unverified. This single exposed synthetic case is not accuracy, throughput, hardware or preferred-model qualification. No unseen paired native-host comparison ran. Earlier timeout/contradiction observations from the superseded bootstrap branch are not relabeled as measurements of this build.

## Open gates

Per-PC hardware/runtime/settings qualification, persistent profiles and durable jobs, unseen final-task outcomes, actual Claude/ChatGPT handoffs, secrets/private-data handling, independent security/dependency/license assessment, sustained load, broader assistive-technology/device checks, Windows equivalence and whole-workflow savings remain open. Program, browser and SDK checks do not close those gates. Hosted CI must be observed on the final pushed commit separately.
