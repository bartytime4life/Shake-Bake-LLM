# Native retrieval versus deterministic preparation

Status: completed development comparison. Both conditions met the frozen rubric
on **8/8 answers**, with no counted required omissions, unsupported claims or
citation errors. Deterministic preparation used **24.35% fewer reported input
tokens**, but median timed workflow was **8.03% slower**. The quality gate passed;
the predeclared efficiency signal did not. Application settings and model
qualification are unchanged.

The first group stopped after one configuration failure, with fifteen attempts
unstarted. The corrected group completed all sixteen. All **17 started
attempts** are accounted for; the setup failure is retained separately.

The prior [host-note diagnostic](host-note-diagnostic-2026-11-05.md) found no
accuracy improvement from imperfect local notes. This next development
comparison asks whether the application's deterministic evidence collection
reduces work when both arms retain competent targeted search over the full
source project. It uses no local model and changes no application settings.

## Results

The [synthetic receipt](../examples/receipts/native-preparation-2026-11-05.json)
contains all sixteen final answers, individual timings/counters, judgments,
identities and the earlier startup failure. Source, requests and private original
answers are unchanged. In one public answer, five exact machine workspace
prefixes were removed from link targets; original/public answer hashes disclose
that normalization. No raw reasoning is published.

| Corrected group | Native retrieval | Same tools plus deterministic brief |
| --- | ---: | ---: |
| Complete / supported answers | 8 / 8 | 8 / 8 |
| Required omissions / unsupported claims / citation errors | 0 / 0 / 0 | 0 / 0 / 0 |
| Reported input tokens | 595,832 | 450,771 |
| Reported cached-input subset | 459,904 | 311,808 |
| Input minus reported cached subset | 135,928 | 138,963 |
| Reported output tokens | 18,129 | 18,723 |
| Median timed workflow, seconds | 62.694 | 67.732 |
| Total timed workflow, seconds | 559.563 | 524.385 |
| Minimum–maximum timed workflow, seconds | 55.651–128.215 | 51.332–83.330 |
| Native commands / nonzero exits | 79 / 4 | 75 / 2 |
| Returned command-output bytes | 1,136,601 | 88,501 |
| Local preparation wall / process CPU, seconds | 0 / 0 | 0.078057 / 0.078035 |

Cached input is a subset of input, not an additional token count. The prepared
arm's input minus cached subset was slightly higher, as was output. None of
these counters establishes billing or subscription-quota savings. The command
audit covered all 154 completed commands; six nonzero exits were expected
no-match searches or changed-file diffs. No prohibited source execution, tests,
edits or network commands were observed. Every source identity and owned-process
cleanup check passed.

| Repetition | Native supported | Prepared supported | Native / prepared median seconds | Native / prepared input tokens |
| --- | ---: | ---: | ---: | ---: |
| 1 | 4/4 | 4/4 | 65.858 / 56.751 | 288,633 / 206,867 |
| 2 | 4/4 | 4/4 | 61.296 / 70.380 | 307,199 / 243,904 |

All four tasks passed in both repetitions and conditions. Dispatch answers
traced the override and both endpoints without inventing traffic; change reviews
explained the failed-commit notification and missing test; log answers recovered
both failures and preserved strict deadline equality; deployment answers retained
unknown inventory/performance and rejected the embedded instruction.

Timing changed direction between repetitions. The native deployment task took
128.215 seconds in repetition one; that outlier affects the smaller prepared
total. The predeclared median criterion was not met. Native runs chose some
broad log/support reads, although the harness permitted targeted search and
never forced a whole-project dump. Tool-output reduction reflects these observed
choices, not a universal native-host limitation.

The unchanged helper selected four files and 705–737 excerpt bytes per task,
with `query_term_budget` and `selection_budget` cutoffs. It omitted controlling
context such as dispatch settings/routing and the change-review contracts;
the log brief also selected one irrelevant utility file. Both arms could
retrieve all source, and the prepared arm still made 75 verification/follow-up
commands. The successful final answers do not establish complete initial briefs.

The next useful proof is a newly frozen, more representative task set and
repeatable total-work measurement with the same native source access. Any
retrieval change needs a separate candidate and new cases; these projects are
now exposed. This result gives no basis for default local-model notes or a
speed/savings claim.

## Frozen comparison design

Four [larger synthetic projects](../benchmarks/native-preparation/README.md)
cover dispatch tracing, a pinned change review, noisy-log failure triage and
deployment unknowns. Each runs twice in each arm: sixteen fresh host sessions.
The baseline receives the exact original request and native search tools. The
prepared arm receives the same request and tools plus the unchanged shipped
`build_brief(..., model=None)` output, using default search limits. Both can
retrieve missing context from the identical full source. No raw repository dump
is forced into the baseline prompt.

Case order is shuffled with seed 1802. Arm order alternates by case and reverses
in repeat two. Host settings inherit the owner's requested `gpt-6-astra` with
`max` effort in CLI `0.162.0-alpha.17.2`. This is a requested identity, not an
independent attestation of the serving model. Each attempt has a 180-second
deadline and 8 MiB limit per captured event/error log. No orchestrator retries
or local inference are allowed. Every started attempt remains in the record.

The native shell permits targeted search and text inspection. Both conditions
use the same restricted filesystem profile: minimal system runtime files plus
the single synthetic project, read-only. Grading keys, other project roots,
authentication files and private records are outside that readable scope.
Tool-network access, web, apps/plugins, MCP, hooks, other agents and memory are
disabled. The host client explicitly sends synthetic task data to the cloud
through the existing signed-in account. Source execution, tests and edits are
outside the task. Actual command records are retained for an action audit.

Named permissions are checked against the installed CLI and an actual local
control before host generation. The [official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
and [evaluation example](https://developers.openai.com/cookbook/examples/partners/harness_aware_plugin_evals/harness_aware_plugin_evals)
describe permission scoping; documentation alone does not establish that this
machine enforced it. The local control checks allowed fixture reads and denial
of outside/symlink/auth-file reads, source writes and socket access.

## Harness checks and retained startup failure

The first separate GPT-6.1 Sol review found that malformed or missing final
answers could halt the schedule instead of failing their case. The corrected
runner validates actions and usage first, then treats invalid final content as
a retained case failure. Unexpected actions and infrastructure failures still
halt. The original unused revision and finding remain archived. Follow-up
review returned no findings. Twenty-three offline runner checks passed,
including real scoped read/write/network controls and two actual owned-process
cleanup regressions. The unchanged application passed all 176 tests separately.

The first started host attempt then exposed a CLI configuration mismatch:
native tools required the installed Code Mode host, which the isolated
configuration had disabled. The runner stopped on the unexpected error item
after 31.577 seconds; no other attempt in that group started. It preserved the
source and stopped its owned process group. This is a setup failure, not an
accuracy result; no final answer from it was used to tune the tasks or rubric.

That attempt's completed-turn counters were recovered separately: 35,814 input,
23,552 cached-input subset and 872 output tokens. Its original runner record
still has null usage because action validation halted before extraction. Across
all 17 starts, recorded host counters total 1,082,417 input, 795,264 cached-input
subset and 37,724 output tokens. Preflight and review work add separate usage
and remain outside those totals. The failed workflow took 32.078 seconds,
including cleanup, and is outside the corrected group's paired comparison.

A new frozen group enables the installed Code Mode host with the same read-only
source/network policy. Its task inputs, source, grading keys, model, effort and
limits match the earlier group exactly. The correction passed the same 23
checks and a separate review with no findings. This is an explicit configuration
repair and restarted comparison, not a discarded failure or an automatic retry.

A separate review of the offline reporting scripts found that a changed label
mapping could attach a grade to the wrong answer. Before grading, the repair
bound every masked task, source, answer and completion status to the frozen
attempt, pinned packet/mapping identities, and checked the returned review's
recorded identity. Six regression checks passed, including swapped labels and
changed reviewed content. Follow-up review returned no findings. The unused
reporting revision and finding are retained; this repair affects offline grade
binding only.

The public fixture generator independently reproduced all 313 files byte for
byte and refused an existing destination. This checks reproducibility and safe
fixture creation; none of the generated source or tests was executed.

## Outcomes and measurements

Frozen required findings and disqualifying claims remain outside the model's
readable roots and prompts. Separate GPT-6.1 Sol AI grading uses per-pair masked
final answers and exact source; the root checked all citations and judgments,
with no disagreements or grade amendments. The reviewer had already seen the
source keys during runner review. One original answer exposed its arm in an
absolute link target, so masking was partial. AI authorship/review is not
authenticated blindness or independent human qualification.

The quality gate requires all eight answers per arm, no critical unsupported
prepared claims, no lost supported baseline case/repetition, and a prepared
supported count at least as high as baseline. Required omissions and false
claims are separate. Missing or invalid final answers fail their case. An
infrastructure failure, unexpected tool type or identity change halts the run;
unattempted cases remain unscored.

Among runs meeting quality, a preliminary efficiency signal requires at least
10% lower total reported input tokens and 10% lower median timed workflow.
This is a predeclared development threshold, not a universal usefulness test or
production promotion. Retain contrary results and do not tune until it passes.

Per-attempt records include preparation wall/CPU time; host and cleanup time;
their sum; CLI input, cached-input subset and output counters; command count,
nonzero command exits and returned text bytes. The prepared brief is recomputed
for every assisted attempt and must equal its frozen exact-source packet.
No worker notes are generated. Hash checks warm the source cache in both arms;
there is no cold-source performance claim. Provider load/cache and per-attempt
runtime context and other workstation activity remain uncontrolled. Two repeats are descriptive, not a
population estimate.

Fixture provisioning, rubric creation, preflight, offline integrity checks,
grading and reporting are outside the timed workflow. Human correction time,
whole-product setup/UI costs, aggregate peak memory and billed/quota savings are
unmeasured. A pass on these artificial projects would not establish real private
repository benefit, unseen correctness, model promotion or broader host
integration qualification.
