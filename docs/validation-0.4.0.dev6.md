# Readiness and evidence-aware preparation — November 5, 2026

This development slice follows the merged `0.4.0.dev5` workbench. Shake & Bake remains standalone, read-only toward inspected projects, and free of required third-party runtime dependencies. Source/model text cannot grant roots, alter policy or authorize commands.

## What changed

The existing Model details disclosure now offers explicit computer and selected-model checks. Computer observations use bounded local kernel metadata: CPU, available logical threads, physical/available RAM, an observable container limit and GPU vendor/device/driver/VRAM when present. Missing values stay unknown. No commands, serial-number reads, source collection or model calls are required for that check. Its fingerprint is a coarse change indicator, not a unique installation identity or attestation.

The model check reads loopback inventory, version and model metadata, verifies the pinned digest and checks runtime stability. It sends no source and requests no generation. Local AI off blocks inventory/model checks; the computer check remains available. Reported context capacity, quantization and capabilities are distinct from requested preparation limits and unmeasured fit/accuracy. Templates and license blobs are not copied into these reports. These fields follow the [official show contract](https://docs.ollama.com/api-reference/show-model-details) and [version endpoint](https://docs.ollama.com/api-reference/get-version).

Successful worker notes now carry observed runtime and exact requested configuration. Runtime drift before/after generation discards the note and retains source. Trial preflight binds the expected runtime across attempts; drift stops further attempts without substitution. A common configuration function drives both wire payload and receipts, correcting the old trial receipt's `keep_alive: 5m` description: actual requests use `keep_alive: 0`, `think: false` and non-streaming generation. These are requests, not runtime attestations; see [chat options](https://docs.ollama.com/api/chat).

Worker input now includes software-produced scan counts, cutoffs and exclusions as bounded data, alongside the unchanged request/excerpts. It does not include roots, routing policy, grading keys or hardware inventory. General instructions distinguish static implications from observed runs and ask only unresolved questions. Notes remain unverified and the host retains final judgment.

## Executed development checks

- 140 source tests pass on Python 3.14.4. New coverage includes unknown hardware, container memory headroom, GPU metadata without invented VRAM, stable fingerprint versus volatile available memory, pinned metadata-only model checks, runtime drift before/after inference, exact wire/receipt configuration, worker-visible scan cutoffs, fixed-scope HTTP authorization and no model traffic while off.
- A clean wheel is checked against every packaged source/web/demo byte and legal notice, then passes 140 tests on Python 3.14.4 from an isolated installed environment with checkout PYTHONPATH unset. The installed shared-controller demo and official SDK 2.3.0 stdio subprocess/shared replays are separate from actual native-host qualification.
- Source and installed checks were repeated after the workspace interruption cleared temporary environments and running services. The private screening receipts survived; no real-model run was silently repeated or relabeled as a check of the replacement execution environment.
- Limited browser checks cover the expanded disclosure, explicit computer/model checks, missing values, selection invalidation, disabled checks when off and phone wrapping. A lost connection now changes the connection label instead of continuing to claim it is connected. Details are in design-qa.md. The selected main design remains unchanged when disclosures are closed.

## Exposed synthetic screening

One evidence-only run and two explicitly selected Qwen 3 candidate runs used all ten exposed Task Lab cases, seed 17 and one attempt per case. Grading keys stayed outside each fixture root and were not sent to the model. No downloads, daemon setup, paid provider or private-source handoff occurred.

| Run | Cases / mechanical checks | Worker failures | Wall seconds | Pipeline identity |
| --- | --- | --- | --- | --- |
| Evidence-only | 10 / 10 | 0 | 0.049542 | `beb0c93124e7ef0ff06f2524bd9b6226157aa1d356a492e68d25e8fdd2d33108` |
| Initial candidate | 10 / 10 | 0 | 161.923510 | `beb0c93124e7ef0ff06f2524bd9b6226157aa1d356a492e68d25e8fdd2d33108` |
| Context/instruction revision | 10 / 10 | 0 | 118.330682 | `dfefedf4d29f3f2016f00a75559e86d97f913da99f65410442c98c387c98c24b` |

Both candidate runs reported model `qwen3:4b-instruct-2507-q4_K_M`, digest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`, runtime `0.40.14`, and the same fixed request options. Initial reported usage: 7,657 prompt / 2,108 output tokens; revision: 9,360 prompt / 2,754 output tokens. Reported loading time differed materially (87.024361541 versus 23.861154279 seconds), so this is not evidence that the revision is faster. Load state and device memory/throughput were not controlled or measured.

Focused Codex inspection found unsupported claims despite all structural checks passing. Initially the change-review note invented a regression involving zero/negative lengths, and the concurrency note implied an observed run without one. The revision explicitly named the file/query scan cutoffs and avoided that observed-run claim, but still falsely suggested that equality validation might permit a length greater than the detected count. In the supplied source, `len(reported) != detected` rejects that input. Both versions also ask some questions about facts already present.

These are qualitative observations from known development cases, not a reviewed accuracy score or isolated causal experiment. Prompt and context changed together. Full semantic review remains PENDING/null in the official sheets; no profile was promoted. No unseen paired native-host baseline or whole-task cloud usage study ran. Both full receipts, checkpoint files and blank review sheets remain private local artifacts; this document contains only the scoped summary.

Follow-up on November 5: the original private screening folders were not located in the checked owner workspace, its parent folders, other checked local artifact locations or connected Drive. The statement above describes the historical run environment; retention in the current workspace has not been verified. Semantic scoring remains pending until the original receipts, outputs and matching review inputs can be recovered. The committed `.dev2` receipts are model-free demonstrations and cannot substitute for these two Qwen runs. A new run would need a new identity and must not be relabeled as either historical attempt.

## Remaining gates

Held-out correctness, complete hardware/runtime/settings binding of qualified profiles, persistent profile storage, automatic tuning, durable job recovery, actual Claude/ChatGPT host UX, secret/export policy, independent security/dependency/license review, sustained load, broad accessibility/device support, Windows equivalence and savings remain open. Passing readiness, JSON checks, exposed cases or SDK transport does not close them. Hosted CI must be observed on the pushed commit separately.
