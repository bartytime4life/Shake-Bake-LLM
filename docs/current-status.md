# Current source, validation and delivery

This guide covers the merged `0.4.0.dev38` purpose-alignment source and its local model screening, and preserves earlier delivery observations below. Use the [quickstart](quickstart.md) to run it, [architecture](architecture.md) for boundaries and [evaluation status](evaluation-status.md) for model/host experiments. Historical counts and research remain attached to their original versions in the [documentation catalog](catalog.md).

## Current reviewed source and screening

Fresh GitHub and fetched-main readback on November 11, 2026 (November 12 UTC) found [PR #74](https://github.com/bartytime4life/Shake-Bake-LLM/pull/74) merged at `c4f25ce41fe854b1b69b839152e94fda27569629`. This dev38 source makes [Ollama junior preparation and ChatGPT/Claude main-developer handoff](product-purpose.md) the primary journey. The worker prompt is `junior_developer_handoff_v2`; previous profiles and model results do not qualify it. See [the implementation validation](junior-main-workflow-2026-11-11.md). Its six [hosted jobs passed](https://github.com/bartytime4life/Shake-Bake-LLM/actions/runs/43154575061) on PR head `ab567355c616d25d5c63d18be668ed7eb5075d2b`; that is distinct from a merge-commit run or owner installation.

The subsequent [frozen local screening](junior-model-screening-2026-11-11.md) ran unchanged dev38 source on forty main synthetic model attempts. All completed mechanically; the source-reviewed AI handoff judgments were 14/20 for `qwen3.5:4b` and 4/20 for `qwen3:8b`. Both failed the quality gate. This exposed, non-blind development review qualifies no profile, final host or savings result. Screening records and guide corrections are on a separate branch based on the merged source; they change no application code. The primary checkout, saved app settings and owner installation were preserved.

The dev38 local checks passed 517 Python tests, 83 dependency-free JavaScript tests plus frontend smoke, source-matching wheel verification, isolated installed smoke/CLI checks, 40 installed handoff tests and the official-SDK subprocess check. The installed browser walkthrough used a simulated Ollama service; exact manual clipboard readback passed after an earlier empty automatic readback. See the linked record for limits and the wheel hash.

## Preserved source and delivery observations

The documentation audit began at **2026-11-12 01:25 UTC** (November 11 in Chicago):

| Record | Observed state |
| --- | --- |
| Remote `main` | `fc639f0dca10ceee784f4d5d5dbf904e06b3c5c1`, dev36, from [PR #71](https://github.com/bartytime4life/Shake-Bake-LLM/pull/71) |
| Reviewed recovery source | `3e59075451e3c1fa74352482ba62adec70827ad8`, dev37; [PR #72](https://github.com/bartytime4life/Shake-Bake-LLM/pull/72) merged into the former feature branch, rather than `main` |
| Documentation branch | `codex/documentation-refresh-20261111` integrates the exact reviewed recovery tree as `62c6fef`, followed by documentation updates, for review into `main` |
| Owner installation | Not updated by this documentation task; an isolated installed preview is separate from the owner's installation |

These are dated observations. Check the [live comparison to main](https://github.com/bartytime4life/Shake-Bake-LLM/compare/main...codex/documentation-refresh-20261111) and current PR state before a merge, checkout update or installation. Merging a feature branch into another feature branch does not establish delivery to `main`. CI, merge, installed version and actual-machine acceptance are separate records.

Check the checkout with `git status --short --branch` and `git rev-parse HEAD`. Use `PYTHONPATH=src python3.12 -m shake_bake --help` for the source CLI; use the installed environment's `shake-bake doctor` and package metadata when checking an installation. Python 3.11+ is required; an unsupported default `python3` is not a valid test runtime.

## Implemented workflows

| Workflow | Current behavior | Remaining boundary |
| --- | --- | --- |
| Failed-run source check | Paste/load a bounded UTF-8 error, explicitly connect/select a project, optionally expand **Run details (optional)**, then select **Find failing source**. Python, pytest, Node.js and TypeScript locations retain source, hashes, associations and gaps. | No failing command, inspected code or repair is executed. A location is not a diagnosis. Unsupported formats and missing source stay incomplete. |
| Recheck and recover | The last accepted report remains visible through pending, failed, malformed or obsolete rechecks. **Download captured JSON report** keeps that exact capture saveable. Copy/text/manual handoff waits while busy or inputs differ. | One report stays in the open tab; a valid replacement supersedes it. Closing/reloading discards failed-run input/report state. Save needed JSON first. |
| Source question | Describe the task/project, select **Prepare brief**, review exact evidence/gaps, then manually copy/save it for an existing assistant chat. A shared activity banner exposes actual preparation status across workflows. | Bounded lexical selection can miss relevant source. No automatic host delivery or final answer is claimed. |
| Source history | Actual result outcome and evidence availability distinguish prepared, incomplete, failed and older completed records. Startup restores the latest usable retained capture without replacing the newer draft. | Source jobs are session-only: at most eight, approximately five minutes. Older metadata without availability facts remains manually reviewable. |
| Optional Local AI | New installations start off. The service saves on/off privately; acknowledged candidate trials require the owner launch flag and pinned installed identity. Preparation mode waits for initialization. | No real model profile is qualified for automatic selection. Metadata readiness does not establish accuracy, measured fit or daemon isolation. |
| Assistant adapter | Optional official-SDK stdio with an explicitly scoped shared connection or separate standalone diagnostic mode. Shared clients use the GUI's routed coordinator/pause policy. | The adapter does not inherit newly connected browser roots. SDK checks do not qualify every host or private-source handoff. |

See [failed-run details](failed-run-workflow.md), [manual handoff](assistant-handoff.md), [draft controls](draft-privacy.md), [Local AI retention](local-ai-preferences.md) and [shared setup](shared-coordinator.md).

## Recorded mechanical validation

The runtime baseline at `3e59075` passed the following checks. These preserved baseline checks are separate from the dev38 checks above and create no new model, host or user-study results.

| Check | Recorded result and scope |
| --- | --- |
| Python core | 516 tests on Python 3.12, Python 3.14 and an isolated installed wheel, with installed imports checked outside the checkout and `PYTHONPATH` unset |
| Browser | 134 scenarios on source and installed builds: 14 readiness, 5 clipboard, 46 workbench, 55 failed-run, 13 session recovery and 1 excerpt/export walkthrough; recovery is invoked once by the failed-run script |
| Dependency-free JavaScript | 75 clipboard/activity, request-deadline and model-readiness checks, plus frontend API, file-launch and server-startup checks |
| Package | Wheel code/assets/legal files match source bytes; installed demo/shared-state smoke passes; no core runtime dependencies |
| Official SDK | Hash-locked SDK 2.3.0 in-process/shared/stdio subprocess checks; subprocess reports five tools and zero model/cloud calls |
| Hosted CI | Six jobs in each [branch run](https://github.com/bartytime4life/Shake-Bake-LLM/actions/runs/43123233890) and [PR run](https://github.com/bartytime4life/Shake-Bake-LLM/actions/runs/43123324301): Python 3.11–3.14, installed-wheel and readiness-browser |

The [dev36 usability record](workbench-usability-2026-11-11.md) and [dev37 recovery record](captured-report-recovery-2026-11-11.md) preserve screenshots, exact scope, earlier failures and the prior wheel hash. A documentation rebuild can change wheel metadata through the root README; do not reuse an older wheel hash as the new artifact's identity. New documentation checks and delivery observations belong in the [refresh record](documentation-refresh-2026-11-11.md) and its PR.

## Open qualification and product work

[Known Issues](../KNOWN_ISSUES.md) remains the issue/gate register and [TODO](../TODO.md) the prioritized work list. Real model accuracy, broader native-host behavior, independent security/private-data qualification, representative usability/accessibility, physical devices, automatic per-PC profiles, durable jobs, Windows support and whole-task savings remain open. Retained experiments include failed quality/efficiency gates. Program tests and exact evidence do not close those gates.

The original owner brief, import checksums, frozen fixtures, model outputs and dated receipts remain unchanged. External model/license/product observations keep their checked dates; this documentation audit does not refresh upstream research or authorize downloads, source sharing, publication or installation.
