# Shake & Bake harness evaluation plan

Test whether a better handoff improves the completed task with the same main
developer model. Use the [harness playbook](agent-harness-playbook.md) to choose
one change. The first candidate is a compact brief that shows the primary
source and the controlling evidence needed to interpret it. Trial Ollama's
notes separately after establishing the evidence-only comparison.

## Start from the observed results

The recorded comparisons give different answers for different endpoints.
A synthetic native-retrieval diagnostic matched answer quality and used less
reported input with a brief, but took longer and failed its preset efficiency
rule. A fresh multi-file orientation study reached more relevant files and used
more tokens. A subsequent comparison found equal file hits with and without
local-model notes, and the dev38 junior-model screen did not qualify its
candidates. Each result belongs to its own task set, prompt, host and scoring
setup. [Evaluation status](evaluation-status.md)

## First development experiment

1. Freeze the source revision, task wording, scoring keys, input and excerpt
   budgets, main host and model configuration, tool access, timeout and maximum
   turns. Save versions for the collector and handoff layout. Pin Ollama's model
   digest, runtime, prompt identity and local settings only in a later
   notes-on experiment. Use public permitted or synthetic source. Keep grading
   keys outside the scanned roots and the answerer's context.
2. Pick development cases with independently enumerated required source
   spans. Include a simple lookup, a multi-file control flow, a config or test
   override, and a case where the deciding evidence is missing or too large
   for the budget. Exercise deterministic failed-run captures and recovery in
   a separate mechanics suite so they do not dilute the source-brief outcome.
3. Run paired, fresh sessions with order alternated across cases. In arm A,
   use today's evidence-only brief. In arm B, use the candidate evidence-only
   brief. Keep both hosts' retrieval permissions and shared budgets identical.
   Add a native-only arm when evaluating whether any handoff earns its overhead.
   Analyze host-with-tools and manual-paste comparisons in separate strata.
   When pasting, apply the same scripted rules for granting follow-up evidence
   to each arm.
4. Score each initial packet and the eventual task outcome separately. Capture
   the same first-answer and final-answer checkpoints for both arms. For
   implementation cases use the same target checks in disposable worktrees.
   Blind graders to the arm and prior results where feasible and record any
   visible clue or shared authorship. Use the existing receipt-bound review
   workflow where it fits. [Host review scoring](host-review-scoring.md)
5. Count malformed output, setup failures, cancellation, timeouts and exhausted
   budgets in the planned denominator. Keep unsuccessful and partial attempts
   with their reasons. Use a fresh held-out cohort only after the development
   gate and candidate are frozen. [Held-out datasets](held-out-evaluation.md)

## Score quality, work and cost

| Measure | Record |
| --- | --- |
| Evidence integrity and coverage | Required file and exact-span hits over fixed denominators, hash and line-range correctness, missing controlling evidence, redundant lines and candidate completeness. |
| Final task quality | Required conclusions or check outcomes met, source support, wrong citations, critical unsupported claims, accepted baseline cases lost, and justified requests for missing evidence. |
| Human effort and runtime | Review and transfer time, source follow-ups, corrections, retries, total elapsed time, and operator interventions. Include local preparation and rework. |
| Usage and machine fit | Measured local inference time and peak memory when available, main-developer input/output and billed/cached usage if observable, and current provider/plan limits if they affect the interpretation. Mark unavailable measurements unknown. |

Before running, choose the smallest practical time or effort gain that would
justify the new format and set a ceiling for any increase in paid-host usage.
The candidate should retain every baseline task pass, introduce zero critical
unsupported claims or stale/wrong-source handoffs, and satisfy the predefined
benefit target. Show per-case outcomes and denominators alongside totals so a
strong easy case cannot hide a loss on a hard case. Keep the current route when
the gain is inconclusive. Track token counts as usage and claim billing or
subscription savings only with evidence at that level.

## Confirm portability and promotion separately

After development, reserve new tasks and keys with a reviewer independent of
candidate tuning. Repeat with the intended receiving host and surface, record
hardware and cold/warm conditions, and retain provenance for each source
snapshot and output. A supported consumer paste path, an actual Codex/Claude
tool connection, a passing wheel and a qualified local model each require
their own evidence. A later notes comparison adds the junior draft to the
same verified packet and holds the main model fixed. Keep automatic selection
subject to the existing qualification requirements.
[Readiness and candidate trials](pc-readiness-and-trials.md) · [Routing](routing-implementation.md)

Use the existing [next trial plan](next-trial.md) and
[development yardsticks](../benchmarks/development-yardsticks.md) for current
runners and fixture rules. Consider Harbor once those runners need controlled
parallel evaluation or shared benchmark task packaging.
[Harbor evaluation framework](https://github.com/harbor-framework/harbor)
