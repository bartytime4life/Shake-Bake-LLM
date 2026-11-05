# Frozen reasoning experiment and separate AI review — November 5, 2026

The Qwen 3 8B prompt experiment is **rejected for shipping**. On the ten known
development cases, six handoffs met the disclosed rubric, matching the earlier
count while losing one previously supported case. The runtime-mode explanation
improved, but the repository-tour note omitted the empty evidence collection.
The current worker prompt and all unqualified routing profiles remain unchanged.

This is a report-only follow-up to [copy recovery and the original 8B
screening](copy-and-screening-2026-11-05.md). The rejected worker source, installed
wheel, frozen plan, every model response, review and amendment are retained
privately. The [sanitized receipt](../examples/receipts/qwen3-8b-reasoning-2026-11-05.json)
contains all ten experimental development notes and their review decisions.

## What was tested

One generic prompt was frozen before generating outputs. It asked the worker to
answer every requested part, preserve expression operands and types, trace a
concrete input, inspect all supplied branches, distinguish absent evidence from
evidence of absence, and offer requested corrections as untested hypotheses.
It contained no case answers. Source remained untrusted data without tools or
action authority. No collection, transport, generation or deadline bound changed.

The frozen development gate required at least seven supported handoffs, at most
two unsupported critical claims, all ten mechanical checks, and preservation of
all six previously supported cases. The experiment passed the mechanical and
critical-claim-count conditions but failed the supported-count and preservation
conditions. New-cohort results cannot reverse that rejection.

The owner PC used the installed `qwen3:8b` Q4_K_M model, reported digest
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`,
with Ollama `0.35.1`. Each case had one attempt: temperature 0, thinking off,
512 output tokens, 8,192 context tokens, a 30-second deadline, a 6,000-byte
message cap and `keep_alive=0`. Seed 17 controls case order; no generation seed
was supplied. These are requested settings and reported identities, not runtime
or weight-byte attestations.

The baseline pipeline is
`3beaa7d1618112b9f5b5c76f4aac07eec897ab3b7b6d9a545d3c5c70ae663b09`.
The isolated experimental pipeline is
`095c422fd28c4c2a79144fc387c40bb5ad1c15865032ca7c759f7c459e6a54e0`.
Its prompt-prefix SHA-256 is
`6a509cc8d4ac2457d808b50557a60ff31e7e1497954d34378733c044ce47ee1c`;
the experimental wheel SHA-256 is
`9cfde98555f0d1c96da1659cda6cb2db4564d395c1c606cc051eb07bddcf5a59`.
The package version remains `0.4.0.dev8`; identities distinguish the experiment.

## Review of the four failures and the new regression

| Case | Experimental result | Source-supported finding |
| --- | --- | --- |
| Failed-test triage | Still incomplete | `attempt > retry_limit` is false at equality. A `>=` hypothesis would satisfy the supplied assertion; wider retry semantics and a rerun remain unverified. The note still omits that requested correction. |
| Change review | Type description corrected; still incomplete | `detected` is a scalar. With `len(reported)=1` and `detected=2`, the earlier range check allows and the later equality check rejects. The note describes both conditions but omits this decisive comparison. |
| Unknown hardware | Still unsupported | An example candidate is not an inventory. The note asserts it is absent, then its question presupposes it is installed. These are two separate unsupported propositions. Throughput correctly remains unmeasured. |
| Runtime mode | Meets rubric | The note now identifies both visible branches, the environment override and the missing environment snapshot, without claiming observed traffic. |
| Repository tour | New omission | The placeholder worker is identified, but the explicitly empty collection is omitted. That was a required finding and was present in the earlier handoff. |

The other five previously supported cases remain supported under the same
central-finding rubric. Explanation gaps and redundant questions are retained in
the receipt rather than silently converted into false-claim counts.

| Development review | Supported handoffs | Decisive misses | Unsupported critical claims |
| --- | ---: | ---: | ---: |
| Original prompt, earlier assistant review | 6/10 | 4 | 3 |
| Frozen experiment, separate AI review with addendum | 6/10 | 4 | 2 |

GPT-6.1 Sol separately reviewed all ten experimental outputs with the exact source
and frozen rubric visible. The root agent challenged one interpretation: saying
an actual input's range is unverified is ambiguous, not demonstrably false when
no runtime input is supplied. The reviewer agreed and removed that unsupported
claim while keeping the missing requested comparison. Both the original review
and addendum are retained. This is an unblinded AI assessment, not independent
human qualification, and the earlier trial is not a randomized control.

## New cases kept outside prompt tuning

After the prompt was frozen, the separate reviewer authored ten compact synthetic
cases without inspecting it: two each clean, defective, no-answer, cross-file and
misleading-comment. Tasks, exact files, expected findings and prohibited claims
were frozen outside the checkout before either model variant ran. The root agent
transferred the records without semantic changes. All ten evidence-only checks
passed. Grading keys remained outside fixture roots and were not sent to Ollama.

The original and experimental installed packages then completed all ten cases
each. Their captured source/context, requested settings, model digest and case
order matched; frozen input hashes remained unchanged. Every output is retained.
No prompt was changed after case authoring or after observing these results.

| New-cohort review | Supported handoffs | Decisive misses | Unsupported critical claims |
| --- | ---: | ---: | ---: |
| Original prompt | 2/10 | 8 | 9 |
| Frozen experiment | 3/10 | 7 | 8 |

Both prompts handled the two no-answer cases without inventing missing facts.
The experiment also handled one clean shallow-copy case correctly. Neither met
the rubric on the defective, cross-file or misleading-comment pairs; both
incorrectly alleged a defect in stable priority sorting. Some notes contradicted
themselves, followed misleading comments over code, or identified a problem but
omitted an explicitly requested example and correction. The independent review
counts these omissions separately from false assertions.

The new-cohort non-regression condition passes, but the earlier development gate
still fails. Eight unsupported critical claims in the experimental cohort also
preclude any accuracy qualification. These small, deliberately challenging case
sets are not a population accuracy estimate. The full new-cohort inputs, keys,
twenty answers and masked judgments remain in the private evidence archive;
the public receipt retains aggregate/per-case counts and identifying hashes.

Variant identities were randomly swapped separately for each case before the
same separate reviewer assessed all twenty outputs against the frozen keys.
The mapping was withheld by instruction, not by an access-control boundary.
The reviewer also authored the cases. The root agent subsequently inspected the
judgments and source. This is separate AI authorship and masked AI assessment,
not blind independent human qualification or proof of unseen training data.
The cohort is now evaluation-exposed and must not be relabeled unseen after
future tuning.

## Validation and retained boundaries

All 176 program tests passed from experimental source and its isolated installed
wheel, with no skips. The installed demo, shared job/evidence and preference
restart checks passed. All 33 packaged code/assets and three legal files matched
source bytes; no core runtime dependency was added. No MCP implementation changed.

The known-case model run completed in 39.071151 seconds. The new-cohort blocks
completed in 36.528819 seconds for the original prompt and 34.814457 seconds for
the experiment. Block order was original first, experiment second; load/cache
state was uncontrolled. These times do not establish a speed improvement, peak
memory, final-task performance or cloud savings.

Two owned temporary loopback daemons ran with `OLLAMA_NO_CLOUD=1` and startup
confirmation, reused existing weights and exited cleanly. Installed manifest
hashes and existing key-file metadata were unchanged. The shared Ollama service
was neither restarted nor reconfigured; no model was downloaded. This is a
configured local-only run, not a network-isolation attestation. Model inference
was local; the separately authorized Codex AI review is a different activity.

The cross-review of the clipboard change found one P2 test gap: keyboard copy
could reuse the preceding native copy. The corrected test writes and verifies a
distinct marker first. All six [hosted jobs passed at `afc181f`](https://github.com/bartytime4life/Shake-Bake-LLM/actions/runs/42116390476),
including source/installed browser checks and the official SDK checks. The actual
owner-PC manual check already used a marker. No additional product defect was
reported in that submitted diff; this is not a complete security audit.

No profile is promoted. Actual final answers in the supported native hosts,
independent human review, broader device/browser behavior, sustained operation,
peak memory and whole-task usage remain open. The next candidate must first pass
development checks without losing existing correct handoffs, then use a newly
reserved cohort and a paired final-host study. Preserve these negative results.

The [next paired thinking-mode diagnostic](thinking-probe-2026-11-05.md) retained
the current prompt and limits. Seven of ten thinking-on responses were truncated
at 512 tokens; only three had complete final JSON. This configuration was also
rejected, with the application unchanged.
