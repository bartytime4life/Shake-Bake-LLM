# Native capabilities and the useful role of a local helper

Checked against primary product documentation on 2026-11-04. Feature availability depends on product, account, operating system and configuration. No account entitlement or installed integration is inferred from documentation. Recommendations below are engineering hypotheses to test, not measured savings.

## What the products already provide

| Surface | Documented capability relevant to this project | Consequence for the comparison |
| --- | --- | --- |
| ChatGPT Work | Uses available files, plugins and approved tools for multi-step tasks; supported desktop workflows can access local resources. | Native retrieval and tool-based processing belong in the baseline. A local helper must add useful evidence preparation beyond those tools. |
| Codex | Repository exploration, editing, local development commands, review, skills and MCP connections. | Compare against focused searches and existing language/development tools, rather than forcing the host to read a raw repository dump. |
| ChatGPT Work/Codex subagents | Separate delegated work and return results; each agent performs additional model/tool work. | A smaller main context does not establish lower total usage. Count delegated work too. |
| Claude chat/Desktop | Connected services and MCP integrations; remote connectors and local desktop integration are distinct access mechanisms. | Test the intended surface and transport explicitly. A working local core is not a verified website connection. |
| Claude Code | Separate-context subagents, code-intelligence plugins, hooks and skills that can preprocess verbose data. | Native log filtering, symbol navigation and specialist delegation are serious alternatives to our helper. Its subagent requests still draw on usage limits. |
| OpenAI API | Built-in search/execution tools, deferred tool discovery, programmatic tool calls and MCP integration. | Batch and filter in code when that suffices. API features must not be described as universally enabled ChatGPT settings. |
| Claude Messages API | Tool discovery, programmatic tool execution, prompt caching and context editing target different causes of context pressure. | Do not assume every reduction requires another LLM or expose every tool definition at startup. |

OpenAI's prompt-caching documentation describes reuse of an unchanged rendered prefix; rewriting earlier context can reduce that reuse. Anthropic distinguishes cached input cost from context size. Therefore compare actual complete-task usage with the native cache behavior retained, rather than judging only the shorter first packet.

ChatGPT's current custom-MCP documentation includes a Secure MCP Tunnel option as well as server URLs, with SSE/streaming HTTP listed. This is a candidate integration route to investigate; it does not validate the current stdio adapter, install a tunnel, or establish availability on the owner's account. No public endpoint is required by our current local-core test. Claude's remote connectors originate from its cloud, whereas local Desktop MCP is a separate mechanism.

## Where local preparation is most worth testing

| Task | Local work | Possible incremental benefit | Accuracy failure to test |
| --- | --- | --- | --- |
| Large repeated CI/log analysis | Deterministically preserve failure blocks; optionally group related failures with a local model. | Avoid repeatedly sending low-value repetition; retain distinct causes. | Grouping merges different faults or drops the first relevant error. |
| Broad codebase orientation | Build a version-bound structural map and retrieve exact definitions. | Reuse local project structure between tasks and hosts. | Stale symbols, hidden branches or incorrect cross-file relationships. |
| PR preparation | Collect changes, affected definitions, callers and relevant existing tests. | Give the host a compact impact map with receipts. | Context outside the diff is omitted and a regression is missed. |
| Repeated local document extraction | Parse fields with page/line references; disclose OCR uncertainty. | Reuse extraction and indexes while keeping the full corpus local. | A number, negation or table association is changed. |
| Local corpus retrieval | Combine exact keyword/symbol search with a measured semantic retriever. | Find relevant material expressed in different words. | Semantic similarity returns plausible but irrelevant evidence or misses exact identifiers. |
| Conflicting evidence | Surface opposing branches and incompatible observations. | Help the host investigate the right unresolved question. | Summarization resolves the contradiction without support. |

These are possible benefits, not unique capabilities absent from the native products. The proposed advantage is reusable local preparation with exact evidence, inspectable coverage and no local-model API bill. The task must demonstrate better or preserved final-answer accuracy against a competent native baseline. Runtime permission and outbound-data policy remain separate from model choice.

## Where to bypass or constrain the helper

Skip an extra model for small questions, exact arithmetic, hashing, file diffs or simple filters that reliable code can do. Existing native tools may already handle a small coding task efficiently. Leave difficult architectural judgments and final review to the host unless a specific local capability has been independently qualified. Fresh web facts need retrieval; an offline model's remembered facts are not current-source evidence.

Use a second local opinion selectively for unresolved contradictions or measured weak spots. Agreement between two models is not ground truth. A host that repeats the worker's error has not gained accuracy. The worker remains preparation, with exact source and explicit unknowns available to the host.

## Accuracy-first evaluation

Run four tracks: a well-configured native host; the same host plus deterministic local evidence; the host plus a fixed qualified local profile; and the host plus task-based routing among qualified profiles. Permit each native host's normal targeted search, code tools and supported context features. Record which features were enabled and include their usage.

Freeze tasks, source versions and the grading rubric before comparison. Separate exposed development cases from unseen qualification cases; keep the reference findings outside worker-readable roots. Measure critical misses, unsupported findings, citation correctness, scope disclosure, useful abstention and final task success. Repeated runs show variation; a finite set cannot establish universal correctness. Human review or another independently justified reference process must settle ambiguous cases.

Reject an efficiency claim if the helper causes additional critical misses or unsupported critical claims. Among profiles meeting the accuracy requirements, compare complete-task time, cloud input/output, cached input, evidence follow-ups, local loading/inference, retries and correction effort. A routed system need not strictly outperform a fixed model to have operational value, but it must preserve the accuracy requirement and justify its added complexity. Keep routing only where it earns that complexity.

This November 4 research snapshot added no subscriptions, paid API experiments or owner-PC installations. Later [evaluation records](evaluation-status.md) include actual local inference, installed/browser checks and scoped Codex synthetic handoff/cancellation. A paired final-host comparison and whole-task usage/savings remain unmeasured; those later checks do not turn the product-documentation hypotheses above into measured benefits.

## Primary sources

- [ChatGPT Work](https://learn.chatgpt.com/docs/get-started-with-work)
- [Codex CLI](https://learn.chatgpt.com/docs/cli)
- [ChatGPT/Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [OpenAI API tools](https://developers.openai.com/api/docs/guides/tools)
- [ChatGPT custom MCP connection](https://developers.openai.com/api/docs/guides/custom-mcp-server)
- [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [Claude connectors](https://support.claude.com/en/articles/11176164-use-connectors-to-extend-claude-s-capabilities)
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code context/cost guidance](https://code.claude.com/docs/en/costs)
- [Claude API context tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/manage-tool-context)
