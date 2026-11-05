# Related-project findings

Reviewed November 4, 2026. These findings come from the projects' source documentation and repository metadata. None of these projects was installed or benchmarked during this task. Published savings remain their authors' results.

## Microsoft TokenEconomizer

Source: https://github.com/microsoft/TokenEconomizer

Closest comparator for reducing repeated coding-agent work. It retains repository-specific lessons, removes unused tools and identifies repetitive failure loops. Its optional repository map uses Aider. Its plugin documentation describes additional model calls through the host agent, so those calls belong in the usage total. The authors report cost reductions; those are not Shake and Bake results.

Decision: add an unchanged host plus TokenEconomizer as an external benchmark arm. Adapt source-backed, invalidatable repository lessons and bounded loop detection. Required review capabilities must remain available; tool removal needs a recovery path. Do not treat a model's loop assessment as authorization to stop or alter host jobs.

## RTK

Source: https://github.com/rtk-ai/rtk

Compresses supported command outputs. Its savings documentation distinguishes output-byte reduction from whole-session token and cost savings; the displayed counts use a bytes/4 estimate. Current documentation separates an Apache-2.0-only OSS edition from editions containing BUSL components.

Decision: evaluate the OSS command filters as an optional adapter using recorded logs first. Preserve complete raw output, exit codes and retrieval handles. Exempt exact source excerpts and patch anchors from lossy transforms. Check the chosen component's license before code reuse or distribution; this research is not a license audit.

## Aider

Sources: https://github.com/Aider-AI/aider and https://aider.chat/docs/repomap.html

Uses a token-budgeted repository map to help select files and symbols. It is a practical reference for our next evidence-selection gate.

Decision: evaluate its map generation through an adapter before implementing an equivalent parser/ranker. Keep commit, dirty-tree and configuration identities in our own evidence layer. A map guides retrieval; it is not evidence that every relevant file has been reviewed.

## Goose

Source: https://github.com/aaif-goose/goose

Provides a local agent host with desktop/CLI surfaces, provider support including Ollama and MCP extensions. Its documentation describes custom distributions. An older lead/worker blog is explicitly marked outdated: that mode and the planning mode that replaced it were removed. Current model workflows need separate qualification.

Decision: evaluate an extension or custom distribution as an alternative to building a desktop shell. Keep Shake and Bake's small, independently testable evidence core. Do not assume the host's broad automation permissions satisfy our project policy or that old lead/worker instructions still apply.

## RouteLLM

Source: https://github.com/lm-sys/RouteLLM

Useful for calibrated stronger/weaker-model routing and benchmark design. Its README says the mf and sw_ranking routers currently use OpenAI embeddings even when a routed model is local.

Decision: use explicit checked task types first. Evaluate a local-compatible routing design later, including embedding locality and hidden usage. Do not add default external embeddings to the private local path.

## Continue

Source: https://github.com/continuedev/continue

Its current README says the project is no longer actively maintained and is read-only. This statement matters even though the repository metadata returned archived=false.

Decision: study model-role and Ollama UX designs; avoid making this a new runtime foundation without a maintenance plan.

## Change to the experiment

Compare the realistic cloud baseline, deterministic collection, Ollama briefings and our routed engine with TokenEconomizer and optional RTK-OSS filters. Use the same pinned tasks, cloud model and outcome criteria; do not stack every mechanism immediately. Include every helper model call, retries, failures and available billing data. Preserve an untouched evidence path for security findings and exact edits.

The first implemented collector remains dependency-free and independent of these external research comparators. Its eight tests do not establish compatibility, security or savings for any external adapter.

## Wider web research and composition

OpenAI's prompt-caching documentation explains that reusable prefixes depend on stable context. Rewriting earlier history or compacting it can reduce cache reuse. Keep stable instructions and unchanged evidence stable within a task; append fresh evidence. Measure any compaction over the rest of the job instead of assuming that fewer tokens must cost less.

Source: https://developers.openai.com/api/docs/guides/prompt-caching

Anthropic's code-execution/MCP article describes loading tools on demand, reducing intermediate data in code and retaining reusable functions. Apply the principle with checked, bounded local recipes; generated code still needs a properly enforced execution environment. This does not authorize execution in the current read-only collector.

Source: https://www.anthropic.com/research/code-execution-with-mcp

LLMLingua-2 studies learned extractive prompt compression. Evaluate it as a later option for prose, with task-specific quality checks. Exact source, patches, user constraints and numeric evidence must remain available unchanged. The paper's benchmark results are not evidence of safety for source editing or of savings here.

Source: https://aclanthology.org/2024.findings-acl.57/

A July 2026 preprint, Token Reduction Is Not Cost Reduction, reports in its indexed abstract that one compression arm removed 38% of estimated raw tool-output tokens while increasing paired cost by 6.8%. This is an author-reported result; full text was not retrieved and the experiment was not reproduced here. It is a useful reason to measure whole-task results rather than output compression alone.

Source: https://arxiv.org/abs/2607.12161

### Proposed composition

Keep one coordinator. It owns task policy, evidence identity, budgets and job state. Repository maps help select evidence. Optional command filters create derived views, each linked to unchanged raw records. Ollama organizes selected material. Cloud providers handle unresolved reasoning through a supported adapter. Every adapter uses the same permission and evidence contracts.

Use Claude Code as the first host, while evaluating Goose as an alternative interface host before building a new desktop shell. Avoid nested full agent loops and stacked output compressors. Provider caching, local result caching and learned repository memory have different identities and invalidation rules.

Primary acceptance becomes preserved task success, evidence quality and lower time/cost per successful job where billing is available. Retain token reduction as a separate metric and the earlier 50% target as provisional. Report helper calls, local compute, retries and incomplete accounting.
