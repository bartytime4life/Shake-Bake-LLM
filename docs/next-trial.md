# Next trial: does the whole helper improve the work?

Planning guidance refreshed November 11, 2026. [Current build
status](current-status.md) identifies the reviewed dev37 code and its
verification scope; this update starts no model, host or user study. The
November 5 actual Codex [synthetic handoff and injected
cancellation/recovery](codex-host-handoff.md) checks remain dated evidence for
that helper/host setup. Current SDK checks do not refresh the hosted trial.

The next host milestone still includes disconnect/deadline/restart coverage
and, after the applicable candidate/source gates, one permitted question
delegated through an authenticated host to local Ollama and returned with
evidence. The earlier observation that Claude Code was signed out was specific
to that inspection; authentication was not rechecked for this documentation
update. Unit tests, simulated HTTP and evidence-only checks do not complete
the milestone. Consumer ChatGPT needs its own supported connection and
independent test; Codex authentication through ChatGPT does not establish it.

## Planning priorities

| Priority | Plan | Concrete acceptance |
| --- | --- | --- |
| 1 | Jobs and correct outcomes | Start with a repository question, a pinned PR review and a failed-test investigation. Write expected findings and acceptable unknowns before evaluation. Execution of inspected-project tests is future work and requires its own isolation design. |
| 2 | Local/cloud division | Collection, search and bounded local preparation stay local. The host receives selected information to reason and answer. Record what crosses that boundary; do not describe cloud handoffs as wholly private. |
| 3 | Models and profiles | Screen explicitly selected installed candidates on development tasks. The shipped worker requests thinking off, 8,192 context tokens, 1,024 output tokens and a shared 30-second deadline; different budgets need a separately frozen experiment, not an undocumented CLI option. Freeze a candidate before a new reserved cohort and consider efficiency only among profiles meeting quality gates. |
| 4 | Connection and recovery | Qualify SDK then actual host, local model availability, timeout, cancellation, restart, changed source and offline failure. Current jobs are session-only; a restart needs a new task. Persistent project memory needs source-version invalidation and a separate design. |
| 5 | Total benefit | Measure correct completed tasks, omissions, false findings, retries, time and cloud usage. Include tool descriptions and follow-up evidence calls, not just the first short brief. |

## Controlled comparison

Use identical pinned source and task text, the same host model/settings, and separate fresh sessions. Use the bundled synthetic Task Lab for exposed development checks only. Reserve new, unseen cases for qualification; do not reuse known answers as blind evaluation evidence.

Dataset split names do not prove independence. The [November 8 frozen
collector comparison](frozen-recall-2026-11-08.md) excluded earlier exposure,
including LCA rows overlapping `dev` and `test`, before opening twelve reserved
cases under its pre-registered protocol. Those cases are now exposed. Its
thirteen remaining reserved rows were an as-of-record count, not a current
blindness audit. A new host cohort needs its own exposure record and must not
inherit a held-out label from a collector-only study.

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

## Retained comparisons and current boundary

The [native-search comparison](native-preparation-2026-11-05.md) is complete.
Both conditions met the rubric on 8/8 answers; deterministic preparation used
24.35% fewer reported input tokens but had an 8.03% slower median timed workflow.
Its initial configuration failure and all sixteen corrected attempts remain
recorded. The unchanged briefs omitted important cross-file context, while the
host could retrieve it through the same tools. Timing changed direction between
repetitions, so this is no repeatable speed or billed-cost result.

That finding motivated a focused change-review design: preserve the requested
diff and collect its contracts, callers and relevant tests without treating
lexical selection as complete coverage. The four native-search cases remain
exposed development material. Any new candidate needs a fresh frozen
comparison with equal native source/tools, cached/uncached input accounted for,
and failure/correction work retained. The subsequent candidate and negative
host results below are historical work, not a newly authorized run.

The initial [deterministic change-review candidate](change-review-candidate-2026-11-08.md)
covers one caller-selected modified file and a supplied exact diff. On a
derivative of the exposed publish-reorder fixture, its packet held five of five
predefined source anchors; the unchanged generic brief held two. This is an
implementation and packet-coverage check, not a final-host comparison or a
qualification result. The candidate is not wired into normal routes or qualified
through held-out evaluation.

The candidate was subsequently frozen for a [two-case synthetic host diagnostic](change-review-host-trial-2026-11-08.md).
An initial four-answer group had no native text tool due to runner configuration;
all attempts and usage were retained. In the corrected group, both native and
prepared arms reached both central conclusions with valid citations, but each
met only 6/8 strict predeclared answer criteria. The prepared arm used 9.1% more
reported input tokens and a 4.6% shorter two-case wall time. The quality gate
failed, and the cases are now exposed development material. The next gate needs
independently authored cases, prompt/rubric alignment, repeated runs and human
grading; neither the packet check nor this paired diagnostic promotes the route.

The [public ReviewBench probe](change-review-public-result-2026-11-08.md) supplied
two independently authored public PRs, two repetitions per arm and equal native
retrieval. After two retained host preflight failures, eight answers completed.
Both arms found the same actuator cache issue and missed source-backed README
issues. Preparation raised reported input and host time, with no demonstrated
quality gain. The public corpus may be model-known and the same AI provisionally
mapped the results; human grading is pending. Use new development tasks for any
redesign and a fresh reserved cohort for qualification. Do not reuse these cases
as unseen evidence or wire this candidate into normal routes.

Other retained [orientation/multi-file
comparisons](orientation-multifile-2026-11-08.md) found more changed-file
coverage in selected arms while using more tokens. Adding the [local model's
draft](draft-comparison-2026-11-08.md) showed no file-coverage effect in its
separate six-case comparison. Those dated cohorts do not qualify a local model,
prove final-answer correctness or establish whole-task savings.

The November 11 [source-span development
diagnostic](source-span-development-2026-11-11.md) independently checks exact
source bytes on six authored cases tailored to known collector changes. Its
pinned dev32/dev35 comparison improves required-span coverage from 11/18 to 17/18
and retains the oversized-anchor miss. This is exposed mechanical evidence,
not a rerun of the host studies above. The [dev36 workbench
review](workbench-usability-2026-11-11.md) and [dev37 capture
recovery](captured-report-recovery-2026-11-11.md) improve task entry, copy and
failure handling without adding a real-model, final-host or savings result.

Linux task core, SDK 2.3.0 transport and scoped actual Codex synthetic handoff/cancellation have evidence. [Current evaluation status](evaluation-status.md) links every retained model experiment, including the 8B prompt comparison, separately authored cohort and bounded thinking-budget diagnostics. The separately authored cohort was kept out of prompt tuning, then became evaluation-exposed; it cannot be reused as unseen. No local profile is qualified. The host-note and native-search development diagnostics do not replace representative final-host qualification or a whole-task savings study. Original `.dev6` outputs remain unavailable. The [external dataset harness](held-out-evaluation.md) supports a newly reserved cohort only after the candidate is frozen. The app stays standalone; future real-project trials require an explicitly approved source root and do not create an application dependency.
