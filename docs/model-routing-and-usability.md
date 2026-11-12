# Goal-first model selection

Implementation status refreshed for the reviewed `0.4.0.dev37` source. See [current status](current-status.md) for source/validation/delivery identity and [the workbench guide](visual-workbench.md) for active controls. The owner-controlled policy engine and `assist` CLI remain available. Automated setup, learned task classification, persisted per-PC calibration and independent model qualification remain pending. No real profile is qualified for automatic selection; the historical shortlist below is not a new recommendation.

The user chooses the work and the desired quality. The system chooses a local model/profile only after that profile has qualified for the task. Accuracy is the default; speed and token counts cannot excuse unsupported answers or critical misses. Model confidence is not a selection certificate.

## Main interaction

| Current control | User wording | Implemented behavior |
| --- | --- | --- |
| Job | Diagnose a failed run / Prepare source brief | The failed-run source check is deterministic and calls no model. Source preparation can use optional, gated Local AI. |
| Task type, under Options | Code, Troubleshoot, Documents, Search | Explicitly select a source-preparation family. It affects profile routing, not deterministic collection. Auto classification is not a current control. |
| Main action | Find failing source / Prepare brief | Read bounded permitted evidence; never run the recorded failing command, apply a fix or label local notes a final answer. Folder connection is explicit beside each project selector. |
| Preparation mode, under Model details | Best tested for this task / Try a candidate — unqualified | Select eligible owner-reviewed records or an acknowledged diagnostic candidate with the launch flag. No qualifying profile keeps evidence-only preparation available. Mode editing waits for initialization/confirmed connection state. |
| Explanation and details | Captured request & job identity / Model details | Inspect the route reason, identity, receipts and reported metadata. Fixed worker settings are not an automatic tuning UI or hardware-accuracy certificate. |

An Auto classifier, Best accuracy quality selector, rich Why this model comparison, arbitrary inference-setting controls, automatic downloads/calibration and connected cloud Send remain design proposals. The current GUI uses manual copy/export into an existing assistant chat; no destination receives source automatically.

The primary path does not require a model-name decision. Show a short model explanation in the result; keep settings available without flooding the workflow. Separate the local-helper status from the connected host's final-answer status and account usage.

Use a device-specific winner claim only after comparable task tests justify it. Before testing, label a candidate unqualified; a shortlist is not a recommendation or measured winner. Never fabricate quality percentages. If several qualified profiles cannot be distinguished reliably, say so and use operational considerations only after accuracy requirements are met.

## Historical category shortlist: November 4, 2026

Historical shortlist checked against the Ollama registry and author documentation on 2026-11-04. Recheck exact tags, licenses and local availability before a new trial or download. These are screening candidates, not detected installations or qualified winners. Local weights are available without per-call model API billing; the connected cloud assistant has its own usage. Hardware, storage and license requirements still depend on the exact release.

| Task family | Initial candidates | What earns the role |
| --- | --- | --- |
| Code review and debugging preparation | `qwen3.5:9b-q4_K_M`, `gemma4:12b` | Critical condition/caller coverage; no invented regressions; exact citations; useful handoff to the host. |
| Harder reasoning and contradictions | `gpt-oss:20b` if runtime headroom permits; `qwen3.8:27b` as a slower/offload candidate | Correct conclusions from conflicting evidence and honest unknowns across repeated held-out tasks. |
| Structured evidence extraction | Qwen3.5 9B and Gemma 4 12B | Field accuracy, source references, preserved negations/numbers and complete required facts. Valid JSON alone does not pass. |
| Lightweight log grouping/triage | `qwen3.5:4b-q4_K_M`, `ministral-3:8b` | Preserve distinct failures and root-cause evidence; meet the same category accuracy gate before speed counts. |
| Screenshots and visual documents, later | Gemma 4 12B and Qwen3.5 9B | Exact critical values, page/image references and disclosed uncertainty. Current worker is text-only; image ingestion is pending. |
| Semantic search, later | `qwen3-embedding:0.6b`, `embeddinggemma-2:270m` | Required-source recall on the user's corpus and resistance to irrelevant matches. Embeddings retrieve candidates; they do not answer questions or certify truth. |
| Larger code-specialist comparison, later | `qwen3-coder:30b` | A reproducible accuracy improvement sufficient to justify loading/offload costs. |
| Exact checks and small filters | Deterministic code, no LLM | Correct calculations, hashes, parses and traceable filtering without an unnecessary generation step. |

The November 4 shortlist used the owner's reported 16 GiB GPUs and roughly 120 GiB system RAM when discussing trial candidates. Historical registry observations put Qwen3.8 27B around 18 GB and Qwen3-Coder 30B around 19 GB; these values have not been refreshed by this documentation audit. They do not prove present installation, available memory, runtime fit or deadline behavior. Separate PCs do not automatically pool memory.

The historical table's “Semantic search, later” entry predates [optional embedding reranking](embedding-rerank-2026-11-07.md). Explicit `--rerank-model` CLI/benchmark use is now implemented and remains off by default; it is not a normal GUI setting. It reorders bounded, already permitted candidates and falls back to lexical order on refusal. It does not add source access or qualify an embedding model's retrieval benefit.

## Setup and model registry

Current explicit computer/model checks and inventory expose reported metadata and unknowns without generation. The proposed first-run setup would add candidate packs, download choices, measured memory fit and calibration. Show any future intended download and let the user start it; no silent downloads, subscriptions or cloud-tag substitutions. Run one candidate qualification job at a time and preserve failures. None of that automatic setup is implied by a readiness check.

The proposed full profile should record model digest, quantization, runtime/driver versions, chat template, prompt/schema versions, thinking mode, sampling, budgets, hardware, task category and evaluation-set version. A result qualifies a profile, not a family. The implemented policy selects owner-reviewed records and enforces pipeline/reported-digest identity; the worker checks runtime stability during use. Full persisted runtime/hardware/settings fingerprinting, automatic setup and independent qualification remain pending. The existing private Local AI preference is not this proposed profile store.

The current policy distinguishes candidate, qualified and disabled, and rejects stale identities, failed records and incomparable trials. Richer testing/failed/stale lifecycle management remains future work. Changed model digests and pipeline fingerprints are gated automatically; the worker also refuses a runtime change during a call. Full persisted runtime/settings/hardware qualification still requires owner review and retesting. Retain a last-qualified profile for rollback.

## Routing rules

1. Establish the task family and source version; preserve the exact request.
2. Do exact collection/search/filtering first. Stop here when it provides a sufficient handoff.
3. Find eligible owner-reviewed profiles for that family and enforced identities; exclude unavailable or stale records. Full hardware-aware profile gating remains proposed.
4. Choose by task accuracy and evidence quality. Account for uncertainty in the evaluation; among indistinguishable qualified options, choose lower total work and acceptable latency.
5. Validate returned structure and source references while keeping source intact. These mechanical checks do not establish semantic correctness; notes stay unverified and missing evidence remains visible.
6. Currently, the user manually copies/exports unresolved evidence to an existing host chat. An automatic cloud-send/escalation policy and acknowledgement UI remain planned. Local-only preparation never silently sends source to a cloud provider.

Do not ask an unqualified classifier to silently choose all other models. Typed task choices and simple deterministic rules can launch the first version. Add learned routing only if it improves measured outcomes against the fixed-profile baseline. Do not run a panel of local models for every question; reserve second opinions for cases where evaluation justifies them.

## Historical shortlist sources, checked November 4, 2026

- [Qwen3.5 family](https://ollama.com/library/qwen3.5)
- [Gemma 4 family](https://ollama.com/library/gemma4)
- [gpt-oss 20B](https://ollama.com/library/gpt-oss:20b)
- [Qwen3.8 27B](https://ollama.com/library/qwen3.8:27b)
- [Qwen3-Coder](https://ollama.com/library/qwen3-coder)
- [Ministral 3 8B](https://ollama.com/library/ministral-3:8b)
- [Qwen3 Embedding 0.6B](https://ollama.com/library/qwen3-embedding:0.6b)
- [EmbeddingGemma 2 270M](https://ollama.com/library/embeddinggemma-2:270m)
- [EmbeddingGemma 2 author card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2)

The registry's metadata and author performance tables may describe different runtime variants. For example, EmbeddingGemma 2's registry lists a larger context than its author overview's 8,192-token specification. Use the actual installed model metadata, supported runtime and a truncation test; do not turn a registry headline into a safe input-budget guarantee. Full-precision published scores also do not establish the score of a particular quantized tag.
