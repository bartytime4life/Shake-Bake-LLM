# Documentation guide

Start with [current evaluation status](evaluation-status.md), the root
[README](../README.md), [TODO](../TODO.md) and [Known Issues](../KNOWN_ISSUES.md).
They describe the current `0.4.0.dev9` behavior and measured limits. Dated reports
below retain the exact scope of earlier checks; an older test count or pending
state is not a statement about the latest build.

## Use and verify the current app

| Topic | Documents |
| --- | --- |
| Local setup and trials | [PC checklist](PC-CHECKLIST.md), [readiness and trial commands](pc-readiness-and-trials.md), [Task Lab](../benchmarks/task-lab/README.md) |
| Interface and recovery | [Visual workbench](visual-workbench.md), [saved Local AI choice](local-ai-preferences.md), [shared coordinator](shared-coordinator.md) |
| Continue in Claude or ChatGPT | [Manual handoff, text-file export and verification scope](assistant-handoff.md) |
| Boundaries and integration | [Architecture](architecture.md), [helper contract](helper-contract.md), [routing](routing-implementation.md), [connection limits](connection-limits.md), [Codex host evidence](codex-host-handoff.md) |
| Evaluation and practical benefit | [Current results](evaluation-status.md), [external datasets](held-out-evaluation.md), [next host trial](next-trial.md), [open gaps](open-gaps.md), [development yardsticks](../benchmarks/development-yardsticks.md) |
| Development and reporting | [Contributing](../CONTRIBUTING.md), [security reporting](../SECURITY.md), [third-party notices](../THIRD_PARTY_NOTICES.md), [licensing plan](LICENSING.md) |

## Current experiment records

Read these as successive experiments with separate identities and preserved failures:

- [Handoff-prompt design and two-model runs](handoff-prompt-2026-11-06.md), where the local model drafts the assistant's prompt.
- [Where host context tokens go at the start of a task](host-context-cost-2026-11-06.md): turn count and broad reads dominate; the brief is cheap but incomplete.
- [Controlling-context collection](controlling-context-2026-11-06.md): bounded definition, usage, test and map additions after the primary windows; measured on the four exposed comparison fixtures, no host run.
- [Web research: what can add value to the brief](research-2026-11-06.md): ten external findings read against the project's thesis, with nine bounded candidates ranked by what can be measured without a cloud run.
- [Retrieval scoring and external recall](retrieval-scoring-2026-11-07.md): BM25-style file scoring, the disclosed distractor exclusion, and the external file-recall adapter, with Task Lab, fixture and self-commit smoke measurements.
- [Independent retrieval audit](independent-retrieval-2026-11-07.md): nine external cases, paired mean/total recall, two primary regressions, truncation, a relevant low-signal exclusion and an exposed-case filter ablation; no model or cost result.
- [A brief Claude and ChatGPT can read directly](handoff-format-2026-11-07.md): the copied brief as Markdown with fenced excerpts, an answer format and verbatim values last; demo size before and after.
- [Datamarking the worker's source](datamark-2026-11-07.md): an off-by-default marker for the local model's copy of excerpts; four Task Lab runs show it did not change the 8B injection draft.
- [Embedding rerank of candidate windows](embedding-rerank-2026-11-07.md): an optional loopback embedding model reorders the top lexical candidates before selection, adding no window; stub-tested, then trialled with `qwen3-embedding:0.6b`: 10/10 Task Lab, one fixture gain, mixed self-commit recall, about seven seconds per case; off by default.
- [Matched-line index](line-index-2026-11-07.md): request-term matches no excerpt covers, listed as line numbers and short texts under byte and count bounds; the log fixture's second failure and the publish contract sentence now reach the brief.
- [Smaller-model screening](screening-2026-11-05.md) and [rejected 1.7B prompt](validation-0.4.0.dev8.md).
- [Installed readiness](pc-readiness-2026-11-05.md), [readiness invalidation](readiness-invalidation-2026-11-05.md), and [copy recovery plus 8B baseline](copy-and-screening-2026-11-05.md).
- [Workbench state and navigation fixes](workbench-fixes-2026-11-05.md) and [browser request recovery](request-recovery-2026-11-05.md), with scoped synthetic regression evidence.
- [Draft context and saving feedback](draft-context-2026-11-05.md), including missing choices, edits during connection and storage failure recovery.
- [Startup brief recovery](startup-brief-recovery-2026-11-05.md), including delayed restoration, newer result ownership and available controls/polling.
- [Page-file launch recovery](file-launch-recovery-2026-11-05.md), including relative assets, a launch guide and separate HTTP-browser versus file-path/VM evidence.
- [Frozen 8B prompt and separately authored cohort](reasoning-screening-2026-11-05.md).
- [Thinking at 512 tokens](thinking-probe-2026-11-05.md) and [the four-arm budget comparison](thinking-budget-2026-11-05.md).
- [Host correction of imperfect local notes](host-note-diagnostic-2026-11-05.md), a separate development diagnostic.
- [Native retrieval versus deterministic preparation](native-preparation-2026-11-05.md): equal supported-answer counts, lower reported input, slower median workflow and a failed efficiency signal; [reproducible synthetic projects](../benchmarks/native-preparation/README.md).

Public receipts contain synthetic evidence and reviewed final notes or answers.
The native comparison discloses removal of machine-specific link prefixes from
one public answer while retaining the exact original privately. Private raw
responses, local settings, captured owner source, stores, keys, environments and
build output do not belong in Git. AI assessments are labeled as such and do not
replace independent human qualification.

## Plans and dated research

[UX workflow](UX-WORKFLOW.md), [per-PC calibration](per-pc-calibration.md),
[calibration GUI](per-pc-calibration-ui.md), [model routing and usability](model-routing-and-usability.md)
and [design gaps](design-gaps.md) include planned work alongside explicitly marked
implemented pieces. A proposed control is not an available feature.

[Model selection](model-selection.md), [native-capability study](native-capability-study.md),
[research](research.md) and [engineering references](engineering-references.md)
retain their dated external observations. Recheck upstream product features,
licenses, model tags and resource requirements before acting on a new candidate.
Published rankings and example tags are not local inventory or owner-PC results.

## Historical records and fixed inputs

The [owner's original source record](planning/source-record.md),
[archive import](import/2026-11-05.md), [first acceptance](first-acceptance.md),
[v0.2 acceptance](v0.2-acceptance.md), [v0.3 acceptance](v0.3-acceptance.md),
[v0.3 development 2](v0.3-dev2-acceptance.md), [v0.3 development 3](v0.3-dev3-acceptance.md),
[dev5 validation](validation-0.4.0.dev5.md), [dev6 validation](validation-0.4.0.dev6.md),
[dev7 validation](validation-0.4.0.dev7.md) and [design QA](../design-qa.md)
preserve their original dates, counts and limitations. New outcomes do not
retroactively qualify them or recover missing original model outputs.

Benchmark fixture Markdown, the inert demo and source examples are evaluation
inputs, not living status pages. Their exact bytes and the original owner request
remain intact during documentation updates.
