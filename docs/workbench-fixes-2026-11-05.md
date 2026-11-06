# Focused workbench fixes

November 5, 2026 · initial local review based on `afc181f`, integrated over `11c6ad1`, still `0.4.0.dev8`. The newer evaluation reports and their open qualification gates are preserved.

## Reproduced problems and corrections

- A failed Local AI update left the checkbox at its optimistic value and allowed task submission. Pending settings now block submission and metadata actions. The interface uses the service's effective value, reconciles failed or lost acknowledgements, and keeps work disabled if confirmation cannot be recovered. Older state responses cannot undo a newer change.
- A delayed history response replaced a brief selected later. History loads now have a revision that is invalidated by another selection, a new task or task completion. Obsolete errors also stay out of the current task's feedback. Expired history entries explain that fresh preparation is needed.
- An initial connection failure stopped all session polling. The workbench now retries state checks and offers an explicit Retry connection button. Captured evidence, JSON export and the task draft remain available during a connection outage. If the service restarted and its session cookie changed, the interface tells the user to save any pinned brief and reload; this does not add durable job recovery.
- Repeatedly selecting Recent briefs on a phone hid the list while leaving that navigation item selected. The selection is now stable; opening a brief returns focus to its heading and preserves the task draft.
- Floating status messages covered the task buttons on a phone. Messages now remain inline beside the task controls until the next action, so they neither cover controls nor disappear while being read. Source panes are labeled, focusable regions with visible focus and native keyboard scrolling. The mode summary describes evidence-only behavior without claiming best accuracy.
- Recorded previews disable task submission, Local AI and metadata actions while keeping the captured brief available for copy/export. Stop is disabled until a starting task has a usable handle.
- Follow-up review reproduced a false pass in the browser test runners: replacing their Python server with `/bin/false` returned exit status zero without running any scenarios. A shared bounded startup check now rejects early exit, spawn failure and missing startup output. All three browser runners fail with exit status one for this reproduction; normal server shutdown no longer prints an expected interruption as an error.

The changes are in the web interface and developer checks. Exact requests, captured source, hashes, source access, model gates and the assistant protocol retain their existing contracts.

## Local validation

- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: **176 passed**, using Python 3.14.4 selected through PATH. The initial shell Python was 3.10.9 and failed because it is below the declared minimum. No support for Python 3.10 is claimed; the existing source launcher already selects an installed supported interpreter.
- JavaScript syntax check, the API-adapter smoke check, **30** model-readiness event checks and **12** clipboard event checks passed.
- **4** actual-subprocess checks cover early server exit, a missing interpreter, a startup timeout and fragmented port output. The browser startup failure guard needs no Playwright installation and runs in the core CI job.
- Isolated Chromium **157.0.8103.38**, driven by the available Playwright **1.56.1**, exercised the source and installed interfaces. The **14** workbench scenarios cover pending, failed and lost setting acknowledgements; policy refusal; unavailable state; initial non-JSON failure and retry; stale state success/failure; four history races; mobile/keyboard/layout behavior; and recorded-preview controls.
- The existing **14** readiness and **4** clipboard browser scenarios also passed for source and installed code. Clipboard checks include exact native readback and a distinct marker before manual keyboard copy. These tests use fresh browser profiles and synthetic source/metadata.
- Layout checks cover widths **320, 390, 600, 850, 851, 1024 and 1440 px**, with reduced motion enabled. Phone screenshots were visually inspected; source panes scroll horizontally by keyboard without causing page-wide overflow.
- An isolated copy was built offline with Python **3.12.3**, setuptools **78.1.1** and wheel **0.46.3**, then installed without dependencies into a fresh environment outside the checkout. The wheel verifier matched packaged code, web/demo assets and legal files to source bytes. Installed startup and shared-service smoke checks passed, including exact synthetic evidence and persistence of Local AI off across restart.

The new workbench browser check is wired into the existing source and installed CI stages. Hosted CI results were not observed during this local review. Packaging configuration and MCP code were unchanged; an official-SDK subprocess check was not rerun for these interface changes.

These checks establish the listed regressions on synthetic inputs and this isolated Chromium setup. They do not establish real-model accuracy, all-browser behavior, assistive-technology qualification, durable jobs, private-source handling, unseen-task correctness or whole-task savings. UX-01, UI-01 and the other broader qualification gates remain open.
