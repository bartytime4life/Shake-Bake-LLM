# Shake & Bake: concept and evidence review

November 8, 2026. Repository baseline: `main` at `f9753fb`, package `0.4.0.dev8`. This review combines current local checks, the owner's [source record](planning/source-record.md), the [evaluation record](evaluation-status.md), and primary research. It is a design decision record, not a product qualification or authorization to inspect private projects, run their code, enable cloud access, or promote a model.

## Executive decision

Keep Shake & Bake as a standalone, local evidence preparation application. Its strongest proved function is bounded, exact, read-only collection with a simple review-and-copy handoff. The next investment should be a **task-specific change-review preparation candidate** that includes the requested diff, affected contracts, callers, and relevant tests, with explicit omissions and retrieval handles. Freeze that candidate, then compare it on fresh tasks against a competent assistant with the same native source access. Do not make local-model notes or generic compression the default: the current project comparisons have not shown a quality or whole-task efficiency gain.

The core contract should remain: the original request and captured source bytes are immutable; paths, line ranges, hashes, scope, and cutoffs travel with the evidence; derived notes remain unverified; only application policy and the user can select roots or authorize actions. Cloud handoff is an explicit boundary crossing, and the receiving assistant can request more evidence.

## What was verified now

| Check | Result | What it establishes |
| --- | --- | --- |
| Python suite on supported `/usr/bin/python3.12` | 177 tests passed | Source-level behavior on synthetic fixtures, including refusal and cancellation paths. No real-model accuracy or independent security assurance. |
| Synthetic retrieval and evidence-only Task Lab | Expected source found in both retrieval variants; 10/10 mechanical coverage checks passed | Required spans, hashes, and cutoffs for exposed development cases. Semantic review remains pending. |
| JavaScript checks | Syntax, frontend smoke, 30 readiness, 16 clipboard, and 4 browser-server checks passed | Deterministic interface logic, not a full owner-browser trial. |
| Isolated Chromium, source and installed wheel | 14 readiness, 5 clipboard, and 33 workbench scenarios passed in each environment | 52 selected browser scenarios per environment, using synthetic data and a fresh profile. Other browsers, real model behavior, and owner workflows remain open. |
| Wheel built from clean `HEAD` in an isolated archive | Byte verifier passed; installed smoke and `doctor` passed from an external virtual environment | Packaged code/assets/legal files match source; packaged demo, shared job, evidence, Local AI setting restart, and startup checks work without a model. |
| Pinned optional `mcp==2.3.0` in an isolated environment | In-process, shared-service, and official-SDK stdio subprocess smokes passed | Five tools, exact synthetic evidence and cleanup work through the installed SDK. This does not certify Claude, consumer ChatGPT, private-source handoff, or model-assisted host work. |

The shell's default `python3` is 3.10.9, below the declared Python 3.11 minimum. That initial run failed in many child-runner and import tests; the supported 3.12 rerun passed. An initial installed-wheel smoke also refused a virtual environment placed *inside* its source checkout, as its isolation assertion requires; the external virtual environment passed. Neither setup failure was treated as a product regression.

## Research findings and implications

### 1. Evidence selection must preserve the answer-bearing context

The [Lost in the Middle study](https://aclanthology.org/2024.tacl-1.9/) found that the models it tested often used relevant information less reliably when it appeared in the middle of long inputs. The effect size cannot be transferred to today's hosts, but it supports position-varied and contradictory-span tests. [ALCE](https://aclanthology.org/2023.emnlp-main.398/) evaluates correctness and citation support separately; a citation-shaped answer can still be wrong or incompletely supported. [Attribute or Abstain](https://aclanthology.org/2024.emnlp-main.463/) likewise distinguishes answer quality from evidence quality and studies explicit abstention.

For Shake & Bake, verify **two stages separately**: (a) whether the packet contains each required span, contradiction, cutoff, and source identity; (b) whether the final assistant answer uses them correctly and states the remaining uncertainty. A hash proves which bytes were captured, not that retrieval was complete or a claim is true. Put key controlling facts near the handoff summary while keeping their full exact excerpts available by reference. Include no-answer and distant-contradiction cases in the new cohort.

### 2. The application must own every trust boundary

[OWASP's prompt-injection guidance](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) describes indirect attacks through external files and retrieved text, and says retrieval or fine-tuning alone does not remove the risk. The [MCP maintainers' tool-annotation analysis](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/) says read-only and other annotations are hints, not enforcement. These sources support the repository's current rule: inspected source, logs, and model output are data, and the application enforces allowed roots, read-only operations, bounded resources, and tool arguments.

Keep the MCP surface small and stdio-only for the initial host path. The [official Python SDK transport guide](https://py.sdk.modelcontextprotocol.io/run/) confirms that stdio needs no listening port and reserves stdout for protocol messages. The repository pins SDK 2.3.0; current upstream SDK and protocol guidance evolves, including [deprecation of MCP client roots in the 2026-07-28 revision](https://py.sdk.modelcontextprotocol.io/handlers/sampling-and-roots/). Root authority should therefore stay in Shake & Bake's own owner-approved configuration, not in a host-advertised root list. Revalidate any SDK upgrade in an isolated wheel and subprocess client before adopting it.

The next security gate is an explicit outbound-content policy for ordinary files, logs, exports, and host handoffs. Screen and preview the exact outbound payload; any redaction must be labeled as a derivative while the original captured evidence stays intact. Secret scanning reduces exposure but cannot certify that all sensitive text was found. Keep cloud calls, inspected-project execution, and writes behind separate permissions and tests.

### 3. Shorter context is an incomplete efficiency measure

The project's [native-retrieval comparison](native-preparation-2026-11-05.md) found 8/8 supported final answers in both arms. Deterministic preparation used 24.35% fewer *reported total input tokens* but was 8.03% slower at the median; the prepared arm's input **excluding the reported cached subset** was slightly higher (138,963 versus 135,928), as was output. This is an observed development result, not a billing result.

[OpenAI's prompt-caching guide](https://developers.openai.com/api/docs/guides/prompt-caching) and [Anthropic's prompt-caching guide](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) explain why raw input, cache reads/writes, output, and actual charge differ. A [2026 preprint on coding-agent compression](https://arxiv.org/abs/2607.12161) reports an author-observed arm with 38% less estimated raw tool output but 6.8% higher paired billed cost, plus damaged verbatim edit anchors in a separate task study. This is external preprint evidence, not a Shake & Bake result; its practical warning aligns with the project's own failed efficiency signal.

Use **correct completed tasks per unit of total work** as the main benefit test. Record all host calls, tool schemas and outputs, retries, follow-up evidence requests, wall time, local CPU/GPU/load, human correction, and provider usage where exposed. Separate uncached input, cached input, cache writes, output, and unavailable billing or quota fields. Preserve exact failure text and edit anchors outside lossy reducers. A shorter first brief earns no savings claim on its own.

### 4. Model notes need independent, task-level qualification

The [host-note diagnostic](host-note-diagnostic-2026-11-05.md) found 9/10 rubric-complete answers with exact evidence alone and 8/10 when the same evidence was accompanied by retained local notes. The assisted arm lost one required uncertainty. The project's larger thinking-budget trials also retained critical unsupported claims. Neither experiment promotes a local model.

[OpenAI's evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices) recommends expert labels and checking model graders against them; model judges can show order and verbosity bias. Use exposed tasks only to develop a candidate. Before a fresh reserved cohort, freeze the prompt, exact model digest, runtime, template, thinking mode, output budget, retrieval policy, rubric, and stopping rules. Keep grading keys outside any source root or model input. Use separate human review for decisive claims; disclose AI-authored tasks and AI grading. Count incomplete, timed-out, refused, and cancelled attempts in the denominator.

The [Ollama API specification](https://github.com/ollama/ollama/blob/main/docs/openapi.yaml) exposes model summary/digest, remote-model fields and thinking metadata; its [usage reference](https://github.com/ollama/ollama/blob/main/docs/api/usage.mdx) defines timing and token counters. These are useful *reported* identities and measurements, not independent proof of weight bytes, hardware fit, or semantic correctness. The project's pre-source compatibility refusal remains appropriate. Keep Local AI optional and off by default; deliberate development trials remain distinct from profile promotion.

## Proposed next experiment

1. Build one deterministic change-review candidate. Input is the unchanged request and an owner-approved pinned diff. Output contains exact changed lines, candidate callers, affected contracts, relevant tests, excluded files, collection cutoffs, and retrieval handles. It does not claim complete review or choose a patch.
2. Freeze source and candidate behavior before collecting a fresh, separately authored set. Include clean changes, cross-file contracts, contradictory comments and executable code, missing tests, distant relevant spans, secrets in ordinary files, changed source after capture, and no-answer cases. Keep the exposed Task Lab and November 5 comparisons as development material only.
3. Compare native host retrieval, the same host plus deterministic candidate, and (only after a separate local-model gate) the host plus exact evidence and local notes. Give each arm equal source access, host settings, and task text. Randomize order, repeat a subset, and retain every failure or setup stop.
4. Adjudicate final task outcomes with a frozen rubric and human review of critical findings, omissions, unsupported claims, citations, useful abstention, and correction effort. A candidate must not lose a baseline-supported case or introduce a critical unsupported claim on the finite acceptance set. This gate is not a universal accuracy guarantee.
5. Promote only if the relevant product gate passes: a demonstrated improvement in useful completed work and acceptable whole-task time/cost, with host, privacy, owner-PC, interruption, and security checks recorded separately. If the candidate misses, retain the negative result and keep the existing evidence-only path.

## Scope of this document

This document incorporates public research and the repository's already recorded synthetic comparisons. The November 8 checks used synthetic/demo material only. No real Ollama inference, private-source capture, authenticated Claude or consumer ChatGPT handoff, independent penetration test, Windows validation, cloud billing analysis, or owner-machine end-to-end qualification occurred here. Upstream documentation and prices can change; recheck them before adopting a new SDK, provider feature, or cost model.

## Subsequent development result

The candidate was implemented and an [exposed packet check](change-review-candidate-2026-11-08.md) was followed by a [frozen two-case Codex host diagnostic](change-review-host-trial-2026-11-08.md). The latter retained a tool-configuration failure and, after correction, failed its strict answer-quality gate in both arms. Those later host calls used only synthetic content and do not change this research review's original verification scope or promote the feature.
