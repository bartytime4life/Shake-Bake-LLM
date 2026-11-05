# Next trial: does the whole helper improve the work?

Actual Codex [synthetic handoff and injected cancellation/recovery](codex-host-handoff.md) checks now pass. The next host milestone is disconnect/deadline/restart coverage and one real question delegated through an authenticated host to local Ollama and returned with evidence. Claude Code was signed out when inspected. Unit tests, simulated HTTP and these evidence-only checks do not complete that milestone. Consumer ChatGPT needs its own supported connection and independent test; Codex authentication through ChatGPT does not establish it.

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

Linux task core and simulated-service acceptance are implemented. SDK 2.3.0 transport and actual Codex synthetic handoff/cancellation have development evidence. Historical `.dev6` screening remains unscored because original outputs are unavailable. New [owner-PC screening](screening-2026-11-05.md) retains a Qwen 3.5 4B timeout and an unblinded Qwen 3 1.7B review: four of ten exposed handoffs met the rubric. Candidate/task quality needs improvement before an unseen study. Broader host orchestration, blind final-task accuracy and savings remain unqualified. The external dataset harness is described in held-out-evaluation.md; no unseen study has run. The source package is self-contained; future real-project trials require an explicitly configured source root and do not create an application dependency.
