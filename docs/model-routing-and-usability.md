# Goal-first model selection

The current `0.4.0.dev8` includes the local graphical workbench; see [visual-workbench.md](visual-workbench.md) and [current evaluation status](evaluation-status.md). The interaction table below includes planned controls, not a claim that every setting is exposed today. The owner-controlled policy engine and `assist` CLI remain available. Automated setup, learned task classification and independent model qualification remain pending. No real profile has been qualified.

The user chooses the work and the desired quality. The system chooses a local model/profile only after that profile has qualified for the task. Accuracy is the default; speed and token counts cannot excuse unsupported answers or critical misses. Model confidence is not a selection certificate.

## Main interaction

| Control | User wording | Behavior |
| --- | --- | --- |
| Task | Code, Troubleshoot, Documents, Search; optional Auto | Choose the task family. Auto may ask a material clarification or return uncertainty; it does not guess consequential requirements silently. |
| Quality | Best accuracy | Select the highest qualified task accuracy under the available hardware and owner-configured resource limits. A slower model may win. |
| Main action | Prepare for my assistant | Collect evidence, run the chosen preparation profile if useful, and hand the supported result to Claude or ChatGPT. This action does not label a local note as the final answer. |
| Explanation | Why this model? | Show the actual task evaluation, model identity, test date and any memory/time tradeoff. |
| Advanced | Models and settings | Manual model choice, exact version, context, supported thinking controls, sampling, limits and receipts. |

The primary path does not require a model-name decision. Show a short model explanation in the result; keep settings available without flooding the workflow. Separate the local-helper status from the connected host's final-answer status and account usage.

Use “Best tested for Code on this device” only after comparable task tests justify it. Before testing, say “Recommended candidate — not tested here.” Never fabricate quality percentages or display an unqualified candidate as the winner. If several profiles cannot be distinguished reliably, say so and use operational considerations only after accuracy requirements are met.

## Category shortlist to qualify

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

The owner's reported 16 GiB GPUs make the smaller generation candidates sensible initial trials. Larger registry packages such as Qwen3.8 27B (about 18 GB) and Qwen3-Coder 30B (about 19 GB) need separate runtime-memory/offload evaluation. The reported roughly 120 GiB system RAM makes some larger local trials worth considering; it is not proof that they meet the deadline or fit today's available memory. Do not exclude a genuinely more accurate model solely to keep all inference on the GPU. Separate PCs do not automatically pool memory.

## Setup and model registry

First-run setup should discover the actual Ollama version, installed model identities, available RAM/VRAM and disk space. Offer a small relevant candidate pack, rather than downloading the entire list. Show the intended download and let the user start setup. No silent downloads, subscriptions or cloud-tag substitutions. Run one candidate qualification job at a time and preserve failures.

Record full model digest, quantization, runtime and driver versions, chat template, prompt/schema versions, supported thinking mode, sampling, context/output budgets, hardware, task category and evaluation-set version. A result qualifies a profile, not an entire model family. Development-3 implements selection from owner-reviewed records, pipeline identity and reported tag-digest checks. Full runtime/hardware fingerprinting, persistent setup and independent qualification remain pending. Store those settings in Shake and Bake's own data store.

The current policy distinguishes candidate, qualified and disabled, and rejects stale identities, failed records and incomparable trials. Richer testing/failed/stale lifecycle management remains future work. Changed model digests and pipeline fingerprints are gated automatically; the worker also refuses a runtime change during a call. Full persisted runtime/settings/hardware qualification still requires owner review and retesting. Retain a last-qualified profile for rollback.

## Routing rules

1. Establish the task family and source version; preserve the exact request.
2. Do exact collection/search/filtering first. Stop here when it provides a sufficient handoff.
3. Find qualified profiles for that family and current capabilities; exclude unavailable or stale identities.
4. Choose by task accuracy and evidence quality. Account for uncertainty in the evaluation; among indistinguishable qualified options, choose lower total work and acceptable latency.
5. Validate the returned structure and citations while keeping source intact. Unsupported claims, incomplete output, missing evidence and disagreements remain visible.
6. Escalate the unresolved question to the connected host when local preparation cannot support it. If the user selected local-only processing, return the limitation instead of sending content to a cloud service.

Do not ask an unqualified classifier to silently choose all other models. Typed task choices and simple deterministic rules can launch the first version. Add learned routing only if it improves measured outcomes against the fixed-profile baseline. Do not run a panel of local models for every question; reserve second opinions for cases where evaluation justifies them.

## Sources

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
