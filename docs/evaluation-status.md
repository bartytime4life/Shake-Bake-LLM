# Current evaluation status

Updated November 8, 2026 for `0.4.0.dev21`. No local model profile is qualified for

Collector file recall, frozen and held out (November 8): the `dev20` collector beat the PR #30 collector on twelve reserved Long Code Arena Python cases under a pre-registered rule, 26 against 23 of 41 changed files reached including the map, with 3 case-level wins and 2 losses. See [the frozen-run record](frozen-recall-2026-11-08.md). This qualifies no model and measures no answer.

Host comparison (November 8): on six real issues with Claude Code subagents, the evidence-only brief did not reduce host tokens or mean tool calls and the hosts named fewer of the changed files (7 against 14 of 25). The pre-registered rule was not met. See [the host-comparison record](host-comparison-2026-11-08.md). The no-tools paste path showed no benefit either (9 against 10 of 25); see [the paste-path record](paste-comparison-2026-11-08.md). A reframed orientation brief then lost no case in twelve paired comparisons on fresh cases but showed no clear gain; see [the orientation record](orientation-comparison-2026-11-08.md).
automatic selection. The latest larger-budget experiment is rejected: both
thinking-on candidates produced six supported handoffs out of ten, retained two
critical unsupported claims and lost a previously supported concurrency answer
to truncation. The shipped worker is thinking off with a 30-second deadline and,
since `0.4.0.dev9`, the `handoff_prompt_v1` design with a 1,024-token cap, under which
the local model drafts the assistant's prompt. These defaults are a bounded baseline, not a qualified model recommendation.

## Retained model evidence

| Evaluation | Observed result | Scope and decision |
| --- | --- | --- |
| Original `.dev6` screening | Original output/review folders unavailable | Unscored historical work; later trials do not reconstruct it. |
| [Fresh smaller-model screening](screening-2026-11-05.md) | Qwen 3.5 4B timed out; Qwen 3 1.7B met the rubric on 4/10 known cases | Retained failures and unblinded assistant review; no promotion. |
| [1.7B prompt experiment](validation-0.4.0.dev8.md) | 4/10 supported, with more unsupported claims | Prompt rejected and reverted; compatibility guard retained. |
| [8B baseline](copy-and-screening-2026-11-05.md) | 6/10 supported; four decisive misses and three critical unsupported claims | Known cases, assistant review; unqualified. |
| [8B frozen prompt](reasoning-screening-2026-11-05.md) | 6/10 supported; a previously supported case was lost | Separate AI review with preserved amendment; prompt rejected. |
| [Separately authored cohort](reasoning-screening-2026-11-05.md#new-cases-kept-outside-prompt-tuning) | Original prompt 2/10; experiment 3/10; nine and eight critical unsupported claims | Cases were outside prompt tuning and are now evaluation-exposed. AI author also graded them; no human qualification. |
| [Initial thinking probe](thinking-probe-2026-11-05.md) | Thinking on at 512: three complete/supported answers, seven truncations | Paired known-case diagnostic rejected; production acceptance unchanged. |
| [Four-arm budget comparison](thinking-budget-2026-11-05.md) | Off/512: 6/10 supported. On/512: 3/10. On/1,024 and on/2,048: 6/10 each, with nine complete answers and two critical unsupported claims each | Forty attempts, separate masked AI grading; both larger budgets rejected. No new reserved cohort started. |
| [Handoff-prompt design](handoff-prompt-2026-11-06.md) | Qwen 3 8B and Qwen 3.5 4B: 10/10 complete drafts each, no worker errors; Qwen 3 4B refused pre-source. Author read: 4B drafts met intent on 10/10, 8B on 7/10 | New worker design, exposed cases, author-only review with instruction tuning between two retained runs; no promotion. |

The subsequent [host-note diagnostic](host-note-diagnostic-2026-11-05.md) completed twenty final answers: **9/10** met the rubric with evidence alone and **8/10** with the same evidence plus retained local notes. Neither arm made a counted unsupported claim or citation error. Both missed the hardware next-evidence request, and the assisted arm additionally omitted the intended-contract uncertainty on the boundary case. The no-regression gate failed; no local profile is promoted.

The [native-retrieval comparison](native-preparation-2026-11-05.md) then used four
new synthetic development projects, two repetitions and identical native tools
in both arms. All sixteen corrected attempts completed: **8/8** answers met the
rubric with native search and **8/8** with the unchanged deterministic brief.
No required omissions, unsupported claims or citation errors were counted.
Reported input fell **24.35%**, but median timed workflow rose **8.03%**; the
quality gate passed and the predeclared efficiency signal failed. The earlier
Code Mode setup failure remains separately accounted for, including usage.
No local model was involved and no profile is promoted.

The local-model cohorts measure source handoffs; the host-note and native
diagnostics measure final answers from explicitly invoked Codex sessions. These
small exposed cohorts are not population accuracy estimates or qualification of
the user's consumer ChatGPT conversation. Missing and truncated responses stay in the denominator. Program-test
passes, valid JSON, evidence references and confident language do not establish
semantic correctness.

## What other checks establish

| Evidence | Established scope | Still open |
| --- | --- | --- |
| Source and installed tests | 176 application tests on the stated baseline; 30 readiness and 12 clipboard Promise checks in each recorded environment | Real-model accuracy, security certification and full owner-PC reliability |
| Hosted checks | Python 3.11–3.14, installed wheel/official SDK, source and installed browser checks; six jobs passed at [the 512-token report revision](https://github.com/bartytime4life/Shake-Bake-LLM/actions/runs/42122640943) | Deployment, model promotion and independent human qualification |
| [Installed readiness](pc-readiness-2026-11-05.md) | Real metadata and selected local browser flows; refresh-status correction | Actual memory fit, broad device/accessibility qualification |
| [Copy recovery](copy-and-screening-2026-11-05.md) | Job-bound feedback, selectable exact text, JSON export and one exact 3,392-character native/manual clipboard transfer; earlier empty readbacks retained | Every browser, permission state and device |
| [Actual Codex smoke](codex-host-handoff.md) | Synthetic evidence-only handoff and cancellation/recovery using an explicitly stopped owned runner | Model-assisted orchestration, disconnect/deadline/restart, private source, Claude and consumer ChatGPT |
| [Larger-budget probe](thinking-budget-2026-11-05.md) | Fourteen focused probe checks, forty recorded attempts and configured cloud-disabled local inference | Production thinking support, unseen accuracy, controlled cold/warm behavior and peak memory |
| [Host-note diagnostic](host-note-diagnostic-2026-11-05.md) | Seventeen private runner checks, including two real process-cleanup regressions; twenty complete host answers; 9/10 evidence-only versus 8/10 with notes under separate AI review | Live helper/model orchestration, unseen accuracy, human qualification and whole-task benefit |
| [Native retrieval comparison](native-preparation-2026-11-05.md) | Twenty-three runner checks, six grade-binding regressions, 313 exactly reproduced fixture files, sixteen complete corrected answers and a separately retained startup failure; 8/8 supported in each arm | More realistic tasks, controlled repeatable performance, correction work, billed/quota savings and human qualification. The AI grader saw keys during preflight and one answer exposed its arm in a link target. |

## Independent retrieval evidence

The [nine-case independent retrieval audit](independent-retrieval-2026-11-07.md)
compares the frozen pre-PR #30 and PR #30 collectors on the same available
Long Code Arena Python cases and budgets. Default mean primary recall rose
5.56% to 16.67%; expanded rose 20.37% to 33.33%, while total expanded primary
hits stayed 4/17, with two case gains and two losses. Expanded excerpts plus
map rose 6/17 to 9/17. Three of twelve fixed-selected cases remain unscored
under the archive cap. A relevant PaddleSpeech file was excluded by the
low-signal rule; neither original arm delivered it. Disabling that rule in a
later exposed-case diagnostic changed no gold-file hit counts.

The original self-commit smoke remains development evidence. New schema-2
receipts replay the same nine exposed cases and reproduce the audit's hit
counts; they are not another independent cohort. The other 38 Python test
cases remain reserved. This establishes bounded retrieval behavior, not a
model qualification, improved host answers, fewer ChatGPT/Claude turns or
cloud-cost savings. No installed application was changed by this audit.

## Shipped behavior and diagnostic boundaries

The worker requests `think: false`, checks declared compatibility before source
submission, and refuses returned thinking, tools, incomplete output and invalid
references. Since `0.4.0.dev9` it requests the `handoff_prompt_v1` structure with
1,024 output tokens; a draft that omits goal or asks falls back to notes only. Routed and explicit candidate paths check reported model digest;
worker/trial records retain runtime and pipeline identity. These checks trust
daemon metadata and do not attest weight bytes or complete hardware qualification.

The earlier 1,024/2,048-token thinking arms used a private frozen diagnostic runner
with thinking on; the shipped 1,024-token cap keeps thinking off. The normal
CLI/workbench has no budget controls, and offline final-content projection
is not an accepted production response. The app remains read-only toward approved
source roots, with no automatic model download or cloud-provider fallback.

## Next gates

1. Freeze a new development candidate or task design that improves useful
   handoffs without critical unsupported claims or lost baseline successes.
   Retain the current negative results; do not retry until a pass appears.
2. Only after that gate, reserve freshly authored cases with keys outside source
   roots. Record AI versus human authorship/review; an owner-declared split or
   instruction-based mask is not proof of independence.
3. Qualify each actual host connection and compare final task outcomes using the
   same source/tasks with native retrieval, deterministic evidence and local
   notes. The local note's score does not prove whether the host corrects or
   repeats its mistakes.
4. Build a focused preparation candidate for one workflow and measure it on
   fresh realistic cases with equal native source access. The first deterministic
   comparison passed quality but failed efficiency; include complete-task time,
   retries, correction work and provider usage before claiming benefit. Peak memory, whole-task savings and a complete
   independent security qualification remain open.

[TODO](../TODO.md) tracks implementation work, [Known Issues](../KNOWN_ISSUES.md)
tracks blockers, and the [documentation guide](README.md) separates current
instructions from dated acceptance and research records.
