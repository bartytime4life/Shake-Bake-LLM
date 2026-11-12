# Model candidates and tuning plan

Historical candidate research checked 2026-11-04; registry facts and published
scores below have not been refreshed for this documentation update. These
observations are not a current inventory or qualified recommendation. Read
[current evaluation status](evaluation-status.md) for measured local results
and the next gate, and [current build status](current-status.md) for code,
hosted-check and installation identity. No shipped profile is qualified for
automatic model selection.

The reviewed dev37 [recovery record](captured-report-recovery-2026-11-11.md)
reports 516 Python tests, 134 source/installed browser scenarios, 75 JavaScript
checks and official SDK 2.3.0 checks. These are mechanical checks, not additional
model trials or a reason to promote the historical shortlist. The owner reported
RTX 5080 GPUs with about 16 GiB each and approximately 120 GiB system RAM on the
PCs; that report is not a fresh capability measurement. Separate PCs do not
automatically combine VRAM, and other workloads reduce available GPU memory.

| Historical role | Candidate | Registry observation on November 4 | Shortlist decision at that date |
| --- | --- | --- | --- |
| Main preparation model | `qwen3.5:9b-q4_K_M` | 6.6 GB download; Q4_K_M | First candidate for code-aware evidence handoffs. |
| Smaller challenger | `qwen3.5:4b-q4_K_M` | 3.3 GB download; Q4_K_M | Compare quality and latency on the same tasks. |
| Alternative family | `gemma4:12b` | Google's model overview estimates 6.7 GB for Q4_0 loading with overhead; this is not an Ollama package-size measurement | Include as a serious challenger, subject to measured runtime fit. |
| Conditional challenger | `gpt-oss:20b` | OpenAI describes deployment within 16 GB using native MXFP4 | Test only if actual GPU headroom is sufficient at our context; published fit is not a guarantee for this workload. |
| Larger experiment | Qwen3.6 27B or Qwen3-Coder 30B | Approximately 18–19 GB and 19 GB registry packages respectively | Outside the initial single-16-GiB all-GPU target; investigate only if smaller models fail quality gates. |

Download size is not runtime VRAM. Model weights, context state, runtime buffers and other applications must be measured on the actual PC. System-RAM offload may permit larger models but can make the helper slower; there is no measured speed result here. The model-family benchmark tables are not results for these quantized candidates on this project.

## What the published statistics tell us

Author-reported results checked 2026-11-04:

| Model | Coding signal | Other relevant signal | Source |
| --- | --- | --- | --- |
| Qwen3.5 9B | LiveCodeBench v6: 65.6 | IFEval: 91.5; BFCL-V4: 66.1 | Qwen 9B model card |
| Qwen3.5 4B | LiveCodeBench v6: 55.8 | IFEval: 89.8; BFCL-V4: 50.3 | Same Qwen table |
| Gemma 4 12B Unified | LiveCodeBench v6: 72.0% | Tau2 average over three domains: 69.0% | Google model card |
| gpt-oss 20B | SWE-bench Verified: 60.7% at high reasoning | Same coding metric: 37.4% low, 53.2% medium | OpenAI model card |

These numbers are screening evidence. Scores across author harnesses, reasoning budgets and quantization setups do not establish a controlled ranking. SWE-bench, LiveCodeBench, IFEval and BFCL measure different abilities; tool-calling performance is indirect evidence for our no-tools preparation worker. None measures faithful excerpts, omitted contradictions or our complete helper workflow. The reasoning-effort variation is a concrete reason to qualify a model-plus-profile rather than a bare model name.

The November 4 research shortlist retained Qwen 9B as the initial reference candidate, added Gemma 4 12B as an alternative, kept Qwen 4B as a smaller challenger, and limited gpt-oss 20B to machines passing a memory check. That shortlist is historical. Choose the next explicitly permitted local candidate using current inventory and the retained failures; qualify its settings before a final-host comparison. No winner is claimed. The independent Artificial Analysis small-model comparison is a secondary screening source; it does not provide RTX 5080/Ollama measurements for our exact candidate profiles.

Pin the selected full model digest, exact tag, quantization, Ollama version, GPU/driver, prompt version and settings. A tag alone can change. The current routed and explicit candidate paths pin the reported digest before and after inference; trial receipts also pin runtime and pipeline identity. This trusts daemon metadata and does not attest weight bytes or enforce the full proposed hardware profile. Do not promote a model based on its own confidence or a published coding benchmark alone.

## Tuning sequence

1. Use the exposed development cases for prompt/settings work. Freeze the final candidate configuration before authoring or reserving a fresh acceptance cohort; keep its keys outside worker-readable roots and do not tune against its results.
2. Compare explicitly selected installed candidates with identical evidence and the strict output schema. The dated 9B/4B shortlist is not a detected installation or a winner; retained 8B measurements are linked in evaluation status. Preserve source text and identifiers regardless of note quality.
3. Compare the shipped `handoff_prompt_v1` baseline (`temperature=0`, 8,192 context tokens and 1,024 output tokens requested, thinking off, 30-second shared deadline) against separately frozen experimental settings. These existing limits are not tuned Qwen3.5 settings, and requested settings do not attest runtime behavior. Low temperature does not prove truth.
4. Discover thinking controls with `/api/show`. Test supported thinking-off and bounded-thinking profiles separately; record defaults when controls are absent. Do not assume every model accepts a boolean switch. The shipped worker explicitly requests `think: false`, refuses declared controls that cannot honor it before source transmission, and rejects returned thinking. Larger-budget thinking experiments are private diagnostics; their final-content projection does not change production acceptance.
5. Change context/output limits only in a separately frozen experiment justified by a measured omission or truncation. The current CLI/workbench does not expose budget controls. The helper receives a small selected packet; it is not using a whole-repository agent context. Record controlled cold/warm loading and measured CPU/GPU offload separately; a first request is not automatically a cold start.
6. Route only tasks for which a profile passed qualification. Do not repeatedly ask several local models the same question by default. A stalled or failed helper returns evidence and a visible failure to the host.

For Claude or ChatGPT, tune task scope and the handoff contract first: one bounded question, compact result, exact evidence fetched as needed, explicit unresolved questions, one coordinator owning retries. This is workflow tuning; no hosted model weights or account settings are changed. Fine-tuning local weights is a later experiment only if repeatable failures remain after retrieval, prompting and sampling changes, with licensed training data and a separate evaluation set.

## Primary sources

- [Ollama Qwen3.5 9B Q4_K_M tag](https://ollama.com/library/qwen3.5:9b-q4_K_M)
- [Ollama Qwen3.5 4B Q4_K_M tag](https://ollama.com/library/qwen3.5:4b-q4_K_M)
- [Qwen3.5 9B author model card](https://huggingface.co/Qwen/Qwen3.5-9B)
- [Gemma 4 author model card](https://ai.google.dev/gemma/docs/core/model_card_4)
- [Gemma 4 loading-memory estimates](https://ai.google.dev/gemma/docs/core.md)
- [Gemma 4 12B registry](https://ollama.com/library/gemma4:12b)
- [OpenAI gpt-oss model card](https://deploymentsafety.openai.com/gpt-oss)
- [OpenAI gpt-oss deployment overview](https://openai.com/index/introducing-gpt-oss/)
- [gpt-oss 20B registry](https://ollama.com/library/gpt-oss:20b)
- [Artificial Analysis small-model comparison](https://artificialanalysis.ai/models/open-source/small/)
- [Qwen3.6 27B registry tag](https://ollama.com/library/qwen3.6:27b)
- [Qwen3-Coder registry](https://ollama.com/library/qwen3-coder)
- [Ollama context and offload guidance](https://docs.ollama.com/context-length)
- [Ollama thinking controls](https://docs.ollama.com/capabilities/thinking)
- [Ollama structured output](https://docs.ollama.com/capabilities/structured-outputs)
