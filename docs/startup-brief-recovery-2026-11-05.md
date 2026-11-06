# Startup brief restoration

November 5, 2026 · follow-up to PR #19, based on `fdba900`, still `0.4.0.dev8`.

## Reproductions and changes

| Issue | Reproduction and impact | Correction |
| --- | --- | --- |
| BUG-015 | Reload with a retained brief and delay its automatic result response. Change task type and complete another task, then release the old response. The old brief replaces the newer result, or its error replaces newer completion feedback. | Startup restoration and manual history selection use one result-loading function with the existing selection/task revision guard. Obsolete successes and failures have no effect on the selected brief or feedback. |
| BUG-016 | Hold the initial retained-brief response after state is connected. Prepare and history remain unavailable, and the polling timers are not started. Changing task type can enable Prepare without completing those startup steps. | Load retained evidence independently of state initialization. Controls, history and polling become available once the current state is ready. Retained evidence continues loading under the same request deadline and result-ownership guard. |

The first defect risks handing off a different captured request/result from the one the user just prepared. Neither reproduction changed inspected source or captured evidence bytes. The correction changes browser result selection and initialization only; the controller, root permissions and session retention are unchanged.

## Verification

- The stale-success reproduction failed against the prior source: the original-request view changed from the new task to the startup task. Separate stale-failure and pending-startup reproductions failed against the prior isolated installed package: an expired-task error replaced successful completion feedback, and Prepare remained disabled while the old result was held.
- Twenty-nine workbench Chromium scenarios pass against source and an isolated installed package. Five are new: delayed startup success/failure after a newer task or explicit history selection, plus a held startup result while a new task starts, polls and finishes. The race cases assert the exact request, handoff text and notice remain unchanged after the obsolete response arrives. New-task race fixtures hold acknowledgement until the real synthetic controller finishes, separating the stale-result defect from the old polling-start delay. The separate polling case returns RUNNING once and requires a later poll to complete before releasing restoration.
- All 176 required offline Python tests pass with Python 3.14.4. JavaScript syntax, API smoke, thirty readiness event checks, twelve clipboard event checks, six request-deadline checks and four browser-server startup checks pass.
- The existing fourteen readiness and four clipboard browser scenarios pass against source and installed code, for 47 scenarios in each environment. Local browser checks use Chromium 157.0.8103.38 and Playwright 1.56.1. Existing mobile, keyboard and recorded-preview cases remain included; no visual design changes were made.
- An isolated offline wheel build used Python 3.12.3, setuptools 78.1.1 and wheel 0.46.3. Wheel verification passed, and all 33 installed runtime/asset files matched final source bytes. Installed startup/shared-job/preference-restart smoke, 176 Python tests and all 47 browser scenarios passed. Packaging configuration and MCP code were unchanged.

The expanded workbench runner already runs against both source and an isolated installed wheel in CI. Hosted results belong to the pull request and are not inferred from local checks.

All browser fixtures use synthetic source and isolated profiles; the real local controller keeps Local AI off. This does not establish real-model behavior, recovery after a service restart, durable results, wider-browser support or formal accessibility qualification. The existing UX-01, UI-01 and REL-01 gates remain open.
