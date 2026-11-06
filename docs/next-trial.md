# Next trial: does the whole helper improve the work?

Actual Codex [synthetic handoff and injected cancellation/recovery](codex-host-handoff.md) checks now pass. The next host milestone is disconnect/deadline/restart coverage and one real question delegated through an authenticated host to local Ollama and returned with evidence. Claude Code was signed out when inspected. Unit tests, simulated HTTP and these evidence-only checks do not complete that milestone. Consumer ChatGPT needs its own supported connection and independent test; Codex authentication through ChatGPT does not establish it.

## Planning priorities

| Priority | Plan | Concrete acceptance |
| --- | --- | --- |
| 1 | Jobs and correct outcomes | Start with a repository question, a pinned PR review and a failed-test investigation. Write expected findings and acceptable unknowns before evaluation. Execution of inspected-project tests is future work and requires its own isolation design. |
| 2 | Local/cloud division | Collection, search and bounded local preparation stay local. The host receives selected information to reason and answer. Record what crosses that boundary; do not describe cloud handoffs as wholly private. |
| 3 | Models and profiles | Screen explicitly selected installed candidates and declared thinking/output budgets on development tasks; freeze a candidate before a new reserved cohort. Prefer the profile that meets quality gates with least total work. |
| 4 | Connection and recovery | Qualify SDK then actual host, local model availability, timeout, cancellation, restart, changed source and offline failure. Current jobs are session-only; a restart needs a new task. Persistent project memory needs source-version invalidation and a separate design. |
| 5 | Total benefit | Measure correct completed tasks, omissions, false findings, retries, time and cloud usage. Include tool descriptions and follow-up evidence calls, not just the first short brief. |

## Controlled comparison

Use identical pinned source and task text, the same host model/settings, and separate fresh sessions. Use the bundled synthetic Task Lab for exposed development checks only. Reserve new, unseen cases for qualification; do not reuse known answers as blind evaluation evidence.

A development comparison of competent native retrieval and deterministic evidence can proceed without selecting a local model. For model-assisted arms, first screen explicitly permitted installed model/profile candidates locally using the [current evaluation record](evaluation-status.md). Dated research shortlists are not installed-model inventories or download instructions. Only after a candidate clears development and reserved-cohort gates, compare the relevant qualified-profile host arms: host with the permitted full source baseline; host with deterministic exact evidence only; host with exact evidence plus finalist A notes; host with exact evidence plus finalist B notes. Randomize arm order, record cold/warm local runs, repeat sufficiently to see variation, and retain every refusal and failed attempt. Freeze a development set separately from held-out decisions so tuning does not leak the answers.

Include relevant evidence near the beginning/middle/end, misleading comments, contradictory branches, no-answer questions, changed files and injected worker notes. Known critical findings must remain detectable; zero additional critical misses on this finite set is a promotion gate, not proof of universal correctness. Unsupported critical claims fail the gate. Investigate any drop in task success or evidence coverage before considering an efficiency win.

Use actual provider usage records when available. If a chat interface does not expose exact usage, label local token estimates as estimates and leave exact billed/quota savings unknown. Track cached/uncached input and output separately. Do not convert token reduction directly into a subscription-limit promise. Include local preprocessing latency, CPU/GPU use, retries and human correction time.

## Bounded host-note diagnostic

The [November 5 host-note diagnostic](host-note-diagnostic-2026-11-05.md) tests
error recovery on exposed development cases before investing in a full benefit
study. It uses fresh cloud-host sessions with identical captured evidence, with
or without existing unqualified local notes. This deliberate error-sensitivity
probe is not the qualified-profile comparison above: it has no native retrieval
arm, live helper integration, unseen cohort or promotion decision. Keep its
results separate from final-host qualification and whole-task savings. All
twenty answers completed: evidence alone met the rubric on 9/10 cases and the
notes-assisted arm on 8/10, with no counted unsupported claims. One missing
intended-contract uncertainty caused a regression; the frozen gate failed.

## Current boundary

The [native-search comparison](native-preparation-2026-11-05.md) is complete.
Both conditions met the rubric on 8/8 answers; deterministic preparation used
24.35% fewer reported input tokens but had an 8.03% slower median timed workflow.
Its initial configuration failure and all sixteen corrected attempts remain
recorded. The unchanged briefs omitted important cross-file context, while the
host could retrieve it through the same tools. Timing changed direction between
repetitions, so this is no repeatable speed or billed-cost result.

The next proposed candidate should address one useful workflow, such as change
review: preserve the requested diff and collect its contracts, callers and
relevant tests without treating lexical selection as complete coverage. Freeze
that candidate before new, more realistic cases. Keep the native baseline's
source access and tools, record cached/uncached input separately, and include
failure and correction work. These four cases are exposed development material,
not a reserved qualification set. No implementation or new host run is implied
by this proposal.

Linux task core, SDK 2.3.0 transport and scoped actual Codex synthetic handoff/cancellation have evidence. [Current evaluation status](evaluation-status.md) links every retained model experiment, including the 8B prompt comparison, separately authored cohort and bounded thinking-budget diagnostics. The separately authored cohort was kept out of prompt tuning, then became evaluation-exposed; it cannot be reused as unseen. No local profile is qualified. The host-note and native-search development diagnostics do not replace representative final-host qualification or a whole-task savings study. Original `.dev6` outputs remain unavailable. The [external dataset harness](held-out-evaluation.md) supports a newly reserved cohort only after the candidate is frozen. The app stays standalone; future real-project trials require an explicitly approved source root and do not create an application dependency.
