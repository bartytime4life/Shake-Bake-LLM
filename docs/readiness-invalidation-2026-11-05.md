# Readiness invalidation correction — November 5, 2026

PR #2 had already merged when this correction began. Inspection of current main
`e598d59edb2d263c867cc3e398b74836e8533319` confirmed that its refresh handler still
rebuilt options without revoking displayed checks. The original review thread
was marked resolved, but that state did not establish a code fix. This follow-up
addresses https://github.com/bartytime4life/Shake-Bake-LLM/pull/2#discussion_r4477744526.

## Resulting behavior

- Selection name/digest and Local AI enable-state transitions revoke metadata and
  trial acknowledgement. A revision counter rejects late success and failure,
  including changes away and back to the original selection.
- Every explicit inventory refresh clears model facts before awaiting inventory,
  blocks another model check during refresh, and revokes in-flight checks even
  if the eventual inventory is unchanged or fails.
- Refresh preserves the exact explicitly selected name/digest pair using the
  option identity, rather than the non-unique model name. A replacement digest
  appears as a separate installed choice; the old pin remains visibly unavailable
  until the operator chooses the replacement. No model is silently selected.
- Disappearance and empty inventories clear old facts. HTTP-success responses
  whose inventory state is unavailable or paused also clear facts and report
  unknown availability. A choice made during a pending refresh is respected.
- A fresh explicit model check is needed to display metadata again. Changes made
  outside the application are only observable on refresh/check/run; this patch
  adds no background model monitoring.

## Local development evidence

Python 3.12.14; Node 24; no real model was used in these checks.

- 30 deterministic JavaScript regression tests pass for both source and isolated
  installed-wheel JavaScript. The initial 29-case suite failed 22 cases against
  untouched main's JavaScript, demonstrating regression sensitivity.
- The source and isolated installed-wheel Python suites each ran 171 tests:
  170 passed and the existing Linux RunnerGate cancellation test failed at its
  two-second ready barrier. That same test also fails in an untouched main
  worktree in this environment. This is an existing test/environment limitation;
  it is not a passing cancellation result and its root cause remains unresolved.
- JavaScript syntax, existing API-adapter smoke, synthetic retrieval and all ten
  evidence-only Task Lab cases pass. These checks do not grade model reasoning.
- Built the wheel without runtime dependencies; verified every packaged code,
  web/demo asset and legal-notice byte against source. The installed doctor,
  packaged-demo/shared-controller and saved Local AI off/restart smoke pass.
- Local Chrome could not reach the workspace's loopback server. Browser policy
  also blocked file URLs; no local browser acceptance is claimed. The new
  isolated GitHub CI job runs 14 real Chromium DOM/event scenarios against both
  source and installed-wheel interfaces over HTTP with synthetic metadata and
  deterministic request barriers. GitHub run 42104211973 passed both sets of
  14 scenarios on Chromium 151.0.7922.34 for commit `909dce5`. All four source
  Python matrix jobs (3.11–3.14), the deterministic UI checks and installed-wheel
  smoke/optional SDK checks also passed in that run. The expanded installed
  full-suite CI step is verified separately on the follow-up commit.

Hosted evidence: https://github.com/bartytime4life/Shake-Bake-LLM/actions/runs/42104211973.
The local RunnerGate failure remains recorded above even though source CI passed.

## Boundaries

The backend, explicit evidence permissions, loopback Ollama restriction and
metadata-only inspection are unchanged. There are no model downloads, activation,
generation, promotion, automatic tuning, or host/cloud handoffs in this patch.
No real Ollama/model experiment was repeated. Reported hardware/runtime metadata
is separate from unmeasured memory fit, performance and semantic accuracy.
Earlier structural successes and incorrect equality reasoning are not repaired
or qualified by this UI change. No model is promoted.
