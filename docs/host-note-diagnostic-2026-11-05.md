# Can the host recover from imperfect local notes?

This is a development diagnostic of error recovery, separate from model
qualification and the planned native-host benefit study. The plan was frozen
before host generation: ten exposed Task Lab cases, each answered in a fresh
Codex session with exact captured evidence alone and with the same evidence plus
the existing local notes. All twenty answers completed. Evidence alone met the
frozen rubric on **9/10** cases; evidence plus notes met it on **8/10**. Neither
arm made a counted unsupported claim or citation error, but the assisted arm
lost one required uncertainty. The no-regression gate was not met. No profile
is promoted and application settings remain unchanged.

## Measured final answers

| Host input | Complete answers | Meets full rubric | Decisive omissions | Critical unsupported claims | Citation errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| Exact evidence alone | 10/10 | 9/10 | 1 | 0 | 0 |
| Same evidence plus retained local notes | 10/10 | 8/10 | 2 | 0 | 0 |

All final answers and separate AI judgments are preserved in the
[synthetic receipt](../examples/receipts/host-note-diagnostic-2026-11-05.json).
The failures are omissions, not incorrect static code conclusions:

- Both hardware answers correctly left installation and throughput unknown,
  but omitted the reference-required request for local inventory and a bounded
  warm/cold measurement. Merely listing unknowns did not meet that full rubric.
- In the assisted boundary answer, the expression, result and documentation
  disagreement were correct. It omitted the required uncertainty about whether
  the code or documentation should change. The evidence-only answer included it.
- Both change-review answers identified the exact newly rejected class,
  `1 <= len(reported) < detected`, and correctly noted the zero/zero change.
  The reviewer accepted that precise class as establishing the reference's
  length-1/detected-2 mismatch without requiring its literal example. The
  earlier local note's ambiguous description was not retroactively regraded.

The host did not repeat the local notes' three critical false claims: it treated
`detected` as a scalar, left candidate installation unknown, and recognized the
visible remote endpoint. Both arms also gave the retry correction as an untested
hypothesis. These are useful recovery observations, but adding notes produced no
new supported case and lost one supported baseline case in this single run.
This small comparison does not establish that notes generally cause omissions.
The root agent checked all twenty answers, source spans and review judgments.

## Fixed inputs and comparison

The source packets and original requests are copied byte-for-byte from the
[four-arm local probe](thinking-budget-2026-11-05.md). They retain evidence IDs,
file/line ranges, hashes and collection limits. Both host arms receive the same
instructions and source text. Only the optional local-note value differs:
`null`, or the unchanged summary, evidence IDs and questions from the earlier
production-accepted thinking-off/512 response. Those local notes supported six
of ten cases and contained three critical unsupported claims. No new local
inference is performed and no failed note is repaired before submission.

Seed 17 shuffles cases. Arm order alternates by case. Each arm runs once, with no
orchestrator retry, in a separate ephemeral session with an empty workspace.
The owner-configured `gpt-6-astra` and `max` reasoning effort are copied into the
otherwise isolated configuration of `codex-cli 0.162.0-alpha.17.2`. These are
requested settings, not independent attestation of the serving model identity.
The existing signed-in account is used; synthetic evidence and optional notes
are explicitly sent to the cloud host.

Tools, shell, web, apps/plugins, hooks, extra agents and memory are disabled for
these host sessions. The app's source, policy, installed model and settings do
not change. The host has a 120-second deadline and each captured event/error log
has a 2 MiB cap. Output must match a common answer schema, name only supplied
evidence IDs and report no test execution. The prompt asks for a concise answer;
it does not impose the local worker's 512-token generation cap.

## Grading and gates

Reference keys remain outside model inputs. All twenty attempts are retained;
missing or invalid answers fail. An infrastructure failure, unexpected action
or changed input stops the run, and unattempted cases remain unscored. Separate
GPT-6.1 Sol review uses per-case masked labels, exact source and frozen keys.
The root agent checks citations and judgments. These are known cases with AI
review, not unseen evidence or independent human qualification. The reviewer had prior
exposure to the cases, and one final answer explicitly mentioned preparation
notes, so the conditions could be inferred.

The diagnostic's positive signal requires ten complete answers in each arm,
no critical unsupported assisted claims, no lost supported baseline answer and
at least as many supported assisted answers as baseline. Citation support is
part of correctness. Completion and the zero-critical-claim condition passed;
preservation of baseline successes and the supported-answer count did not. A
pass would have shown only recovery from these particular notes under this
setup, without promoting the local model or establishing useful added value.

## Runner checks

Seventeen offline checks passed before generation. They cover exact paired
source preservation, unknown or duplicated references, invalid usage, missing
or unexpected host events, forbidden actions and claimed test execution. Two
real subprocess checks establish cleanup when a host exits but a child survives
and when a running host ignores graceful termination.

The pre-generation cross-review found one cleanup issue. Revision 1 is retained
with that finding and was never used for a host request. Revision 2 keeps an
owned session anchor alive through group termination and forced cleanup, then
reaps it; the follow-up review found no issues. Host response time and cleanup
time are recorded separately. These checks validate the diagnostic runner's
specified behavior, not the application's broader cancellation qualification.

The unchanged application's 176 unit tests also passed under Python 3.12.
The 64 tracked application, test, packaging and integration files were checked
against the preserved owner checkout and are byte-identical. This report adds
documentation and a synthetic receipt, without changing application behavior.

## Observed time and host counters

| Host input | Input tokens | Cached input tokens | Output tokens | Sum of host elapsed time | Median host elapsed time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Exact evidence alone | 121,375 | 11,008 | 11,369 | 315.760 s | 33.740 s |
| Evidence plus notes | 122,567 | 11,008 | 12,214 | 371.419 s | 33.439 s |

Cached input is a reported subset of input, not an additional token total.
The longest host responses were 40.247 and 80.299 seconds respectively. Elapsed
time includes host startup and trace validation; process cleanup is recorded
separately, totaling about 5.013 seconds per arm. All responses arrived within
the fixed 120-second deadline. No host tools were used and every owned group
was stopped; all attempt workspaces remained empty.

These are one-run counters and timings, not a cost or quota calculation. Cache
state, provider load and per-attempt runtime context were not controlled;
requested model identity was not independently attested. Larger total elapsed
time alongside a similar median does not establish a general speed effect.
Both arms received the same evidence, so this design does not measure savings
from source reduction. The earlier local preparation cost and separate AI review
are outside these host counters.

## What this does not measure

Both arms receive identical bounded evidence. There is no native retrieval arm,
full-repository baseline, live helper/MCP delegation or local-model orchestration.
Host-reported input, cached-input and output counters and elapsed time are
recorded, but billed usage, subscription quota, local preparation/loading,
controlled cache state, peak memory and human correction work are not measured.
Review work adds separate usage. No whole-task savings follows from these data.

The [current evaluation index](evaluation-status.md) and [next trial](next-trial.md)
keep local accuracy, host correction, actual integration and practical benefit
as separate questions. No newly reserved cohort is spent on this diagnostic.

The next practical development comparison is competent native retrieval versus
deterministic evidence preparation on larger tasks where collection may save
work. A local-note arm still needs its own quality justification. Preserve these
negative results; do not lower the rubric or spend a newly reserved cohort to
turn this run into a pass.
