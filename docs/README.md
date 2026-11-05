# Documentation guide

Start with [current evaluation status](evaluation-status.md), the root
[README](../README.md), [TODO](../TODO.md) and [Known Issues](../KNOWN_ISSUES.md).
They describe the current `0.4.0.dev8` behavior and measured limits. Dated reports
below retain the exact scope of earlier checks; an older test count or pending
state is not a statement about the latest build.

## Use and verify the current app

| Topic | Documents |
| --- | --- |
| Local setup and trials | [PC checklist](PC-CHECKLIST.md), [readiness and trial commands](pc-readiness-and-trials.md), [Task Lab](../benchmarks/task-lab/README.md) |
| Interface and recovery | [Visual workbench](visual-workbench.md), [saved Local AI choice](local-ai-preferences.md), [shared coordinator](shared-coordinator.md) |
| Boundaries and integration | [Architecture](architecture.md), [helper contract](helper-contract.md), [routing](routing-implementation.md), [connection limits](connection-limits.md), [Codex host evidence](codex-host-handoff.md) |
| Evaluation and practical benefit | [Current results](evaluation-status.md), [external datasets](held-out-evaluation.md), [next host trial](next-trial.md), [open gaps](open-gaps.md), [development yardsticks](../benchmarks/development-yardsticks.md) |
| Development and reporting | [Contributing](../CONTRIBUTING.md), [security reporting](../SECURITY.md), [third-party notices](../THIRD_PARTY_NOTICES.md), [licensing plan](LICENSING.md) |

## Current experiment records

Read these as successive experiments with separate identities and preserved failures:

- [Smaller-model screening](screening-2026-11-05.md) and [rejected 1.7B prompt](validation-0.4.0.dev8.md).
- [Installed readiness](pc-readiness-2026-11-05.md), [readiness invalidation](readiness-invalidation-2026-11-05.md), and [copy recovery plus 8B baseline](copy-and-screening-2026-11-05.md).
- [Frozen 8B prompt and separately authored cohort](reasoning-screening-2026-11-05.md).
- [Thinking at 512 tokens](thinking-probe-2026-11-05.md) and [the four-arm budget comparison](thinking-budget-2026-11-05.md).
- [Host correction of imperfect local notes](host-note-diagnostic-2026-11-05.md), a separate development diagnostic.

Public receipts contain synthetic evidence and reviewed final notes. Private raw
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
