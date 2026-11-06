# Browser request recovery

November 5, 2026 · follow-up to the workbench fixes merged in PR #17, based on `6d62d65`, still `0.4.0.dev8`.

## Reproductions and changes

| Issue | Reproduction and impact | Correction |
| --- | --- | --- |
| BUG-010 | Hold a browser state or setting response indefinitely. The initial connection has no Retry action, or the setting remains pending and blocks preparation indefinitely. | A 15-second browser deadline covers both response headers and the JSON body. Aborting releases the pending UI action; retry and setting reconciliation use the existing service checks. |
| BUG-011 | Let the service accept a task, then drop its acknowledgement. The old browser immediately enables another submission without checking the accepted task. A successful response without a valid task ID also leaves an active job that cannot be polled or stopped. | Uncertain start responses disable new work until session state is checked. The interface resumes observing a retained running job and directs the user to Recent briefs for completed work. Starts are never automatically retried. Missing or malformed task handles enter the same recovery path. |
| BUG-012 | Fail a job-status request, then return successful RUNNING responses. The old interface keeps showing the service as unavailable because state synchronization only ran when idle. | State synchronization also runs while a job is active and the connection is unconfirmed. The progress text describes unknown status during the outage; a fresh state check restores the connection controls. |

These are workflow/recovery defects in the browser interface. The affected behavior needs these fixes before promotion. The reproductions use synthetic source; they did not show inspected-source mutation or altered evidence. Cancelling a browser HTTP request does **not** establish that an accepted service operation or an Ollama job stopped. The service's existing execution, connection and cancellation limits remain separate.

## Verification

- The initial stalled-state browser case failed against `6d62d65` because no retry appeared after advancing the browser clock beyond 15 seconds. Separate lost-start and active-polling cases also failed against an isolated installed copy whose app.js bytes matched that commit.
- Six deterministic API checks cover stalled headers, a stalled body, deadline cleanup, unchanged request fields, unreadable acknowledgement, explicit refusal versus uncertain server timeout, and invalid task handles. They exercise the actual API adapter with virtual deadlines and an AbortSignal-aware transport.
- Nineteen Chromium workbench scenarios pass against source and isolated installed code, including five new recovery cases. Real browser fetch requests are held or dropped at the test route; only the two stalled-request cases advance the browser clock. The lost-start cases first send a synthetic task to the real local controller, then drop its acknowledgement. They verify that only one start was sent and distinguish completed-history recovery from resumed running-job monitoring. A test rerun exposed an ambiguous fixture that allowed either state; the cases now select their intended state explicitly.
- The existing fourteen readiness and four clipboard browser scenarios pass. Checks use Chromium 157.0.8103.38 and Playwright 1.56.1 with isolated browser profiles.
- The required offline Python suite passes all 176 tests with Python 3.14.4. JavaScript syntax, API smoke, thirty readiness event checks, twelve clipboard event checks and four test-server startup checks pass.
- An isolated offline wheel build used Python 3.12.3, setuptools 78.1.1 and wheel 0.46.3. Wheel verification passed, and all 33 installed runtime/asset files matched the final source bytes. Installed synthetic startup/shared-job/preference-restart smoke and all 37 browser scenarios passed; no model or cloud host was used. Packaging configuration and MCP code were unchanged.

The deadline tests and all nineteen workbench scenarios are included in source and isolated installed-package CI checks. Hosted results are recorded on the pull request rather than inferred from local checks.

This is browser recovery within the existing running session, not durable job recovery, exactly-once execution or a real-model cancellation qualification. Briefs can still expire. Browser timer throttling or suspension can delay a deadline. Restart, wider browsers, assistive technology, sensitive-source handling, real-model behavior and the broader UX-01/UI-01/REL-01 gates remain open.
