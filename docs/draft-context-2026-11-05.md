# Draft context and saving feedback

November 5, 2026 · follow-up to PR #18, based on `d71959b`, still `0.4.0.dev8`.

## Reproductions and changes

| Issue | Reproduction and impact | Correction |
| --- | --- | --- |
| BUG-013 | Store a request for one project/task type and conflicting separate preferences. Reload restores the request but selects the preferences' project/type. If the saved project is unavailable, the old interface silently selects the demo. | Restore request, project ID and task type from the same draft record. Missing projects and unsupported task types require explicit approved selections before preparation; retain the request. The submit handler also rejects missing choices. |
| BUG-014 | Make browser storage reject writes, then type while the initial state request is pending. The saved older request can replace the new text when connection completes. Later editing failures have no saving feedback. | Track fields edited during initialization, defer writes until saved context is resolved and preserve those edits even when storage is unavailable. Persistent text below the request distinguishes page-only retention, saved drafts and saving failures. Successful later input updates the status and saved record. |

These are browser draft association and retention defects. The checks use synthetic requests and source. Draft data supplies only text and identifiers, never root grants or policy. The service still validates project IDs and task types. Pinned results keep their original request and evidence; editing the next draft does not rewrite them.

## Verification

- The conflicting-preferences browser check failed against the prior implementation: it selected `another-demo` instead of the draft's `starter-demo`.
- Twenty-four Chromium workbench scenarios pass against source and the isolated installed package, including five new cases: conflicting saved preferences; missing project and explicit replacement; typing/task-type changes during initial connection with failed storage; unsupported saved task type; and visible saving failure followed by recovery and reload. The last case preserves Unicode, line breaks, leading/trailing whitespace, project/type and the prior pinned handoff text. These are assertions on the browser textarea's value, not arbitrary input-file byte preservation.
- The existing fourteen readiness and four clipboard browser scenarios pass. Local browser checks use Chromium 157.0.8103.38 and Playwright 1.56.1 with isolated profiles and a real synthetic local controller. State metadata and storage failures are injected; the controller keeps Local AI off, and no model or cloud host is used.
- All 176 required offline Python tests pass with Python 3.14.4. JavaScript syntax, API smoke, thirty readiness event checks, twelve clipboard event checks, six request-deadline checks and four browser-server startup checks pass.
- The mobile saving status was visually inspected at 390 pixels. Existing workbench checks still cover seven viewport widths, keyboard source scrolling and inert recorded-preview actions. This is not a formal accessibility or assistive-technology audit.
- An isolated offline wheel build used Python 3.12.3, setuptools 78.1.1 and wheel 0.46.3. Wheel contents verification passed; all 33 installed runtime/asset files matched final source bytes. Installed startup/shared-job/preference-restart smoke, 176 Python tests, all 42 browser scenarios and the readiness/clipboard/request event checks passed. Packaging configuration and MCP code were unchanged.

The expanded workbench script already runs against both source and an isolated installed wheel in CI. Hosted results belong to the pull request and are not inferred from local checks.

## Limits

Drafts remain automatic, browser-origin localStorage records. Clearing browser data or using another port/profile can lose access to them. A failed save leaves the prior stored draft unchanged; keep the current page open or copy the request before leaving. Opt-out/clear controls and cross-tab coordination remain planned. Project IDs do not attest root identity: this change does not detect an owner reusing an ID for a different folder. Briefs remain session-only and can expire. Wider browser, real-model, sensitive-source and durable recovery qualification remains open.
