# Known issues and release expectations

Updated November 5, 2026 · applies to the 0.4.0.dev8 development build.

This register separates implemented controls from open engineering work and unverified behavior. An open security qualification gap is not a confirmed exploitable vulnerability. No complete independent security audit, real-model accuracy qualification or production-readiness sign-off has been completed. The existing 176 passing offline program tests cover specific contracts only.

## Release blockers

A known defect causing any of the following blocks the affected release or feature promotion:

- Disclosure of source, credentials or other private data beyond the user's permitted boundary.
- Unauthorized execution, model-directed actions, or mutation/corruption of inspected source.
- A bypass of authorization, evidence integrity, model identity or qualification gates.
- A known critical accuracy regression, including a missed critical finding or unsupported critical claim in the acceptance evaluation.
- Silent loss of results or a failure that defeats required stop/recovery behavior for the feature being released.

Unverified gates remain pending; absence of a demonstrated exploit does not complete qualification. Do not mark all open items fixed because a test suite passes. A narrower development preview may document its limits explicitly, but must not imply that blocked production features are qualified.

## Open register

| ID | Status | Issue or missing qualification | Current limit / required next evidence |
| --- | --- | --- | --- |
| UX-01 | OPEN — workflow gap | Setup, GUI, prepared assistant adapter, qualification and handoff are not one guided shared-state experience. | Shared mode now uses one routed controller via a private scoped local bridge; native tests cover shared jobs/pause/cancel. First-run help and result-identity labels are implemented; full setup/calibration, actual host delivery, other durable settings and job recovery remain pending. Local AI on/off persists in private service state; SDK transport has development evidence. See docs/shared-coordinator.md and docs/UX-WORKFLOW.md. Browser qualification is still open. |
| LIC-01 | OPEN — distribution review | Exact external dependency/model artifacts are not fully cleared for public redistribution. | Existing app MIT text is unchanged; THIRD_PARTY_NOTICES.md and MODEL_LICENSES.json inventory sources and pending work. Pin/check actual dependency/model artifacts before public distribution. Bundled code evaluations now use self-contained synthetic fixtures. |
| SEC-01 | OPEN — qualification gap | Secrets may occur inside ordinary source files, captured evidence or exports. | Filename exclusions are not complete secret detection. Define permitted handling, preview/redaction behavior and adversarial tests before sensitive-data handoff qualification. No automatic cloud client is implemented. |
| SEC-02 | OPEN — qualification gap | Dependency, optional-SDK and update provenance have not been fully qualified. | Record exact versions/origins, review dependency risk, verify update/package integrity and run the applicable integration checks. No verified automatic updater is claimed. |
| SEC-03 | OPEN — qualification gap | No complete independent security review has assessed the actual boundaries. | Review source access, local web requests, worker/parser behavior, model trust and exports. Record findings and closure evidence. This register is not that audit. |
| SEC-04 | OPEN — qualification gap | Hostile input, connection-load and resource-exhaustion resistance are incompletely tested. | Connection admission, idle/absolute deadlines and recovery now have six real-socket regression checks; see docs/connection-limits.md. Broader malformed input, sustained load, memory bounds and representative-machine behavior remain unqualified. No full connection-flood resistance claim. |
| SEC-05 | DOCUMENTED LIMITATION | Loopback binding and session/CSRF checks do not provide a separate multi-user security boundary. | Current scope is a trusted local owner session. Do not expose publicly or claim isolation between local users/processes. Shared/remote use requires a separately designed and tested authorization boundary. |
| SEC-06 | DOCUMENTED LIMITATION | Model checks rely on trusted daemon metadata; they do not attest loaded weight bytes or isolate daemon egress. | Keep the daemon trusted and cloud-disabled. Verify actual deployment/network policy separately; model identity checks are not proof of its entire runtime behavior. |
| ACC-01 | OPEN — feature promotion blocker | No real model is qualified. Retained smaller-model and 8B prompt experiments include reasoning errors and regressions. A separately authored cohort produced only 2/10 supported original handoffs and 3/10 experimental handoffs. In the latest forty-attempt comparison, thinking off scored 6/10; thinking at 1,024 and 2,048 also scored 6/10, with one truncation and two critical unsupported claims each. Both larger budgets lost the previously supported concurrency case and were rejected. See [evaluation status](docs/evaluation-status.md) and [budget results](docs/thinking-budget-2026-11-05.md). | Keep profiles unqualified and production acceptance unchanged. A new development candidate, newly reserved cohort, paired final-host comparison and human qualification remain needed. The previously separate cohort is now exposed. Original `.dev6` outputs remain unavailable. Valid JSON, compatibility guards and AI grades do not close this gate. |
| ACC-02 | DOCUMENTED LIMITATION | Bounded lexical retrieval can omit relevant evidence. | Exact spans, hashes and cutoffs are retained; they are not an exhaustive repository review. Test unseen large/cross-file cases and disclose missing context. |
| REL-01 | OPEN — qualification gap | Real-machine interruption, failure recovery and model behavior remain unqualified. | Test unavailable models, timeouts, cancellation, source/model changes and restart on actual PCs. Ctrl+C checkpoints exist; hard-crash resume and durable GUI job recovery do not. Disconnecting does not prove the Ollama daemon stopped work. |
| UI-01 | OPEN — qualification gap | Earlier limited Chrome checks and a new local in-app-browser metadata/demo walkthrough have scoped evidence; broader accessibility/device qualification remains open. | See design-qa.md and docs/pc-readiness-2026-11-05.md. The follow-up verified persistent pending/completion feedback, selectable text and JSON export, with earlier empty clipboard readbacks retained. The final installed synthetic brief passed exact native and manual keyboard readback (3,392 characters); broader clipboard/browser qualification remains open. See docs/copy-and-screening-2026-11-05.md. Chrome automation could not navigate in the earlier session. Formal assistive-technology and wider-device review remain open. |
| INT-01 | OPEN — partial evidence, feature promotion blocker | SDK 2.3.0 installed stdio/shared replay and actual Codex synthetic handoff/cancellation checks passed. Claude/consumer ChatGPT and broader host behavior remain unqualified. | docs/codex-host-handoff.md records request/source integrity, project/busy refusals, paused AI, cancellation of an explicitly stopped owned runner, refused cancelled evidence and a fresh successful task. Disconnect/deadline/restart, actual model-work cancellation, model-assisted orchestration and private-source handling remain needed. Qualify each supported connection separately; these checks do not close the gate. |
| CAL-01 | PLANNED | Explicit capability/model metadata checks and per-call runtime stability now exist. Automatic per-PC tuning, persisted profiles, full hardware/runtime/settings identity enforcement and the complete dashboard remain unimplemented. | Follow the per-PC calibration and GUI specifications. Existing model/pipeline gates do not enforce the entire proposed device profile. |
| PLAT-01 | UNSUPPORTED | Windows does not have a qualified equivalent to the current Linux process/read boundary. | Do not present the build as a verified Windows application. Design and test the equivalent boundary before support. |
| MET-01 | UNMEASURED | Cloud savings, full-task efficiency and real local memory/throughput are unknown. | Preserve failures and missing usage; measure successful tasks on actual hardware and supported hosts. No token/quota or universal best-model claim. |

The source-reader limitations also include trusted root ancestors, hard links/bind mounts, and lack of an atomic whole-repository snapshot. Child resource limits are not a complete OS filesystem/network sandbox. See README.md, docs/helper-contract.md and docs/open-gaps.md for current boundaries.

## Selected fixes verified in the development environment

| ID | Status | Reproduction / expected behavior | Fix and evidence |
| --- | --- | --- | --- |
| BUG-001 | VERIFIED CLOSED — stated development cases | Hold incomplete local requests, including headers that drip faster than an idle timeout. Admission stays bounded, stalled connections expire, and normal requests recover. | Eight-handler cap, three-second initial idle timeout and cooperative twelve-second connection deadline. Real-socket tests cover idle, drip, excess connections, incomplete authorized body and close/recovery. Broader SEC-04 qualification remains open. |
| BUG-003 | VERIFIED CLOSED — stated restart cases | Local AI off was lost after restart, and a stale browser start could resume the service. | Private service preferences retain explicit on/off across restart; a new installation starts off. Task creation no longer changes that setting. File-failure, isolation and stale-client regressions pass; see docs/local-ai-preferences.md and docs/validation-0.4.0.dev7.md. |
| BUG-002 | VERIFIED CLOSED — queued-expiry case | Delay the controller so a queued task request times out before execution. It must not start work later after the caller sees a timeout. | Cancel the pending future when its wait expires; the regression check verifies that no task/child is created. This does not cancel an operation already running. |
| BUG-004 | VERIFIED CLOSED — stated refresh cases | Refresh installed models with the same name/digest selected. Facts clear correctly, but the readiness status incorrectly continues to say the refresh is running. No source or model selection is affected. | Report refresh completion explicitly and request a new model check. Four existing synthetic refresh cases fail before the fix and pass afterward; all 30 readiness tests pass against source and installed code. The corrected installed in-app browser also shows completion with real unchanged-inventory metadata. See docs/pc-readiness-2026-11-05.md. |

| BUG-005 | VERIFIED CLOSED — stated feedback/recovery cases | A delayed browser clipboard request had no pending feedback, allowed duplicate writes and could finish after another brief was pinned. Completed feedback disappeared after five seconds. | Persistent job-bound status, one unsettled browser write, selectable read-only handoff text and preserved JSON export. Original-request JSON encoding preserves CR/CRLF through the text fallback. Twelve synthetic Promise cases cover late success/failure, missing API, retry and exact text; the installed in-app browser verifies the stated feedback/selection cases. The final installed synthetic brief also passed exact native and manual clipboard readback; wider browser qualification remains UI-01. See docs/copy-and-screening-2026-11-05.md. |

These scoped closures do not close the independent audit, owner-PC, real-model or broader load gates. Earlier receipts remain versioned history.

## Bug handling expectations

Each important bug record must contain:

1. A stable identifier, affected build/component and status.
2. Reproduction steps and expected versus actual behavior, using a synthetic or sanitized fixture where possible.
3. Impact and release-blocker decision, including whether evidence or private data was affected.
4. The fix or mitigation, plus a regression check that exercises the failure rather than merely mirroring implementation.
5. Recorded verification on the relevant platform/profile; distinguish simulated-service checks from real model, browser or owner-PC results.

Use OPEN, REPRODUCED, FIXED — AWAITING VERIFICATION, and VERIFIED CLOSED as distinct states. A mitigation is not automatically a completed fix. If a defect cannot be reproduced, retain the report and uncertainty rather than silently deleting it. Avoid credentials and private source in public bug reports; a private reporting channel still needs to be selected before a public release.

Prioritize security-boundary violations, data loss and critical accuracy regressions first; then broken workflows, recurring hangs and inaccessible essential controls. Minor cosmetic defects may remain in a visible known-issues list when they do not conceal status, evidence or errors. Classification must follow impact rather than the apparent size of the code change.

Release evidence should identify the package/build, tests and applicable real-machine checks, remaining limitations, rollback/recovery instructions and disposition of every blocker. Safe updates, authenticated reporting and public release automation remain engineering work, not claims made by this document.
