# Next trial: does the whole helper improve the work?

The next milestone is one real question delegated through Claude Code to local Ollama and returned with evidence. Unit tests and simulated HTTP do not complete that milestone. ChatGPT integration needs its own supported connection and independent test; it is not assumed from Claude Code support.

## Planning priorities

| Priority | Plan | Concrete acceptance |
| --- | --- | --- |
| 1 | Jobs and correct outcomes | Start with a repository question, a pinned PR review and a failed-test investigation. Write expected findings and acceptable unknowns before evaluation. Execution of inspected-project tests is future work and requires its own isolation design. |
| 2 | Local/cloud division | Collection, search and bounded local preparation stay local. The host receives selected information to reason and answer. Record what crosses that boundary; do not describe cloud handoffs as wholly private. |
| 3 | Models and profiles | Compare pinned 9B/4B candidates, supported thinking modes and context/output budgets on held-out tasks. Prefer the profile that meets quality gates with least total work. |
| 4 | Connection and recovery | Qualify SDK then actual host, local model availability, timeout, cancellation, restart, changed source and offline failure. Current jobs are session-only; a restart needs a new task. Persistent project memory needs source-version invalidation and a separate design. |
| 5 | Total benefit | Measure correct completed tasks, omissions, false findings, retries, time and cloud usage. Include tool descriptions and follow-up evidence calls, not just the first short brief. |

## Controlled comparison

Use identical pinned source and task text, the same host model/settings, and separate fresh sessions. Use the bundled synthetic Task Lab for exposed development checks only. Reserve new, unseen cases for qualification; do not reuse known answers as blind evaluation evidence.

First screen the eligible model/profile candidates locally, including Gemma 4 12B and gpt-oss 20B when runtime memory permits. Then compare four arms: host with the permitted full source baseline; host with deterministic exact evidence only; host with exact evidence plus finalist A notes; host with exact evidence plus finalist B notes. Randomize arm order, record cold/warm local runs, repeat sufficiently to see variation, and retain every refusal and failed attempt. Freeze a development set separately from held-out decisions so tuning does not leak the answers.

Include relevant evidence near the beginning/middle/end, misleading comments, contradictory branches, no-answer questions, changed files and injected worker notes. Known critical findings must remain detectable; zero additional critical misses on this finite set is a promotion gate, not proof of universal correctness. Unsupported critical claims fail the gate. Investigate any drop in task success or evidence coverage before considering an efficiency win.

Use actual provider usage records when available. If a chat interface does not expose exact usage, label local token estimates as estimates and leave exact billed/quota savings unknown. Track cached/uncached input and output separately. Do not convert token reduction directly into a subscription-limit promise. Include local preprocessing latency, CPU/GPU use, retries and human correction time.

## Current boundary

Linux task core and simulated-service acceptance are implemented. Actual Ollama inference, SDK interoperability, host orchestration, blind review accuracy and savings remain unverified. The source package is self-contained; future real-project trials require an explicitly configured source root and do not create an application dependency.
