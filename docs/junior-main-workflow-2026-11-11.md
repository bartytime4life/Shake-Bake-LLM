# Junior developer to main developer workflow

November 11, 2026 (America/Chicago), local `0.4.0.dev38` candidate on `codex/junior-main-workflow-20261111`, based on fetched main `93bd8e7`. This record describes implementation and synthetic mechanical checks. It does not qualify a real Ollama model, receiving assistant, owner installation or subscription savings.

## Problem and resulting behavior

The owner clarified that Ollama should do local junior developer preparation, producing output to paste into ChatGPT or Claude as the main developer. The prior start screen led with failure diagnosis, put the Local AI control inside Options and described a generic evidence helper. The existing worker drafted a prompt without explicitly naming these developer roles.

The app now opens **Prepare source brief**, explains the role split, exposes **Local AI — Ollama junior developer**, and keeps detailed setup behind **Model details**. Both browser text layouts and CLI renderers tell the receiving assistant to act as the main developer, verify the local preparation, make final decisions and propose implementation/checks for the original request. Results disclose whether a junior draft is included, unavailable or unused. Failed-run handoff is explicitly evidence-only and names the same main-developer role.

The changed worker instructions are versioned as `junior_developer_handoff_v2`. They ask the local junior to investigate supplied evidence, draft focused asks and next checks, and leave final diagnosis/design/implementation decisions with the main developer. Output fields, generation settings, evidence collection and local transport boundaries are unchanged. Existing pipeline identity checks prevent previous profiles from silently qualifying changed code. No model is promoted.

[Product purpose](product-purpose.md) maps components, authority and acceptance. README, project instructions, architecture, quickstart, workbench/handoff guides, current status, evaluation status and TODO use that direction. The recovered owner brief, archive records and dated receipts remain intact; the exact owner clarification is an append-only addition to the source record.

## Local verification

| Check | Observed result |
| --- | --- |
| Required core suite | `PATH=/usr/bin:$PATH PYTHONPATH=src python3 -m unittest discover -s tests -v`: **517 passed**, Python 3.12.3. Tests use synthetic fixtures and simulated transports. |
| Worker instruction budget | Ten evidence IDs fit within 4,096 bytes: 3,097 bytes normally, 3,260 with the experimental datamark instruction. No model was called. |
| JavaScript | Syntax checks pass; **40** clipboard/activity/handoff, **30** model-readiness, **6** request-deadline, **3** file-launch and **4** server-startup tests pass, plus frontend API smoke. Clipboard tests cover role/status truthfulness in both layouts and exact original request retention. |
| Wheel | Built with setuptools 84.2.1 and wheel 0.48.0 using no-index/no-dependency/no-build-isolation mode. Packaged code, demo/web assets and three legal files match source bytes; no core runtime dependencies. |
| Isolated installation | Fresh Python 3.12 environment, `PYTHONPATH` unset, outside the checkout: package identity is dev38, installed demo/shared-state and Local AI restart smoke pass. Both installed CLI text layouts contain the main-developer role, evidence-only disclosure and expected exact synthetic source. All 40 clipboard/handoff checks also pass against installed app.js. |
| Official SDK | Hash-locked MCP 2.3.0 environment with this installed wheel: official-SDK stdio subprocess/shared-GUI smoke passes, five tools, zero model calls, zero cloud calls and successful connection-publication cleanup. |
| Browser walkthrough | Actual installed wheel in the in-app browser, using only the bundled inert demo and a simulated loopback Ollama service. Scope and limits are below. |

Wheel SHA-256: `214a3737f3cc2ef2648ac76f2d262f29c5aa58e32e04363a2c4f60445e6c4c72`.

Earlier local test failures were stale expected prompt/layout values and an assertion placed in the new test rather than the original test. They were corrected before the final pass; the earlier failures remain in the task tool history and final successful logs are retained locally. The full browser regression matrix is left to hosted CI; this walkthrough does not repeat or claim the historical 134-scenario result.

## Captured product-flow review

Screenshots were captured and inspected from this run, with private state and synthetic captures retained outside Git. The before screen and prepared-brief view show the generic description and hidden model controls. Installed after views show the new primary journey, actual draft/evidence status and supporting failed-run evidence.

1. **Start and task entry — clear in the checked desktop view.** Source preparation opens first; the junior/main roles, Local AI control and exact next action are visible. New private state starts Local AI off. Existing folder approval and synthetic-demo labels remain explicit.
2. **Model preparation and review — passed for the synthetic paths.** Local AI off produces a labelled evidence-only brief. Enabling Best tested with no qualified profile also remains evidence-only. An acknowledged `fixture:local` candidate produces a validated, visibly unverified junior draft; its summary explicitly says no real Ollama model ran. Closing Options correctly collapses the external Model details control's accessible expanded state.
3. **Handoff — reviewed text and manual transfer verified.** Both text layouts contain the main-developer instruction, included-draft disclosure, original request JSON and synthetic note. The copy button reports browser success. The first automated clipboard readback was empty; that observation is retained and is not a verified automatic transfer. **Select all text**, followed by native keyboard copy, returned exactly the reviewed full-evidence handoff: 4,881 characters. Clipboard results are specific to this browser/session and synthetic text, not cloud delivery or all-device acceptance.
4. **Failure evidence — passed for the labelled example.** The separate source check preserves its example error and exact matching line, gives a main-developer handoff and explicitly says no Ollama draft was used. It does not execute the recorded command or claim a verified cause/fix.

The simulated service observed exactly three `/api/tags`, one `/api/show`, two `/api/version` and **one `/api/chat`** requests across the walkthrough. The chat request belonged to the explicitly acknowledged candidate trial. No actual Ollama generation or paid host session ran. Those counts do not attest a real daemon's cloud setting.

The first [dev38 hosted run](https://github.com/bartytime4life/Shake-Bake-LLM/actions/runs/43153861204) passed all four Python 3.11–3.14 jobs and the installed-wheel/SDK job. Its browser job passed readiness and clipboard checks, then stopped at a prior assertion that Local AI was hidden inside Options. The follow-up updates that assertion to require the intentionally visible junior-developer control, closed detailed setup and truthful evidence-only result. A new complete hosted pass must be observed separately.

The [next hosted run](https://github.com/bartytime4life/Shake-Bake-LLM/actions/runs/43154167979) also passed the source workbench, excerpt/export and 55 failed-run scenarios, then stopped in session recovery: a fixture connected a folder in the new default source workflow but subsequently read the failure workflow's project selection. Recovery fixtures now explicitly choose the failed-run workflow before their folder-connection tests, preserving the intended session-only approval and late-acknowledgement checks.

Tall full-page result capture failed in the browser tool. Viewport captures were accepted only after the correct result had visibly painted; a partial/blank intermediate image was rejected. Native controls, accessible labels, draft disclosure and reference-text review were observed. This is not a full accessibility, assistive-technology, mobile/device or representative usability qualification.

## Remaining gates

Screen the changed worker prompt on development tasks, then freeze a candidate before fresh held-out cases and separate human review. Compare direct native chat, evidence-only preparation and junior-assisted preparation on identical permitted inputs. Count the whole cloud task, local preparation time, retrieval, follow-ups, retries, corrections and failures. Retain unknown provider usage and separate subscription/quota/billed observations. Earlier results cannot qualify the changed prompt or prove savings.

This work used an isolated branch and installed test environment. The primary checkout and owner installation were preserved. Publishing the branch, hosted CI, merging and owner-machine installation are separate delivery observations; use the associated PR and live source identity for those states.
