# Whole-workflow user experience

November 4 design plan, with implementation status refreshed November 6, 2026 for `0.4.0.dev8`. See [evaluation status](evaluation-status.md) for current evidence and remaining gates.

This plan joins setup, local preparation, evidence review, assistant handoff and recovery into one product journey. It is grounded in the current HTML/JavaScript, GUI controller, helper and prepared SDK adapter. It is not a screenshot audit or a completed user test. The earlier cloud-browser inspection was blocked and remains a historical limitation. Later [installed readiness](pc-readiness-2026-11-05.md) and [copy-recovery](copy-and-screening-2026-11-05.md) walkthroughs cover selected local flows; broader desktop/phone and accessibility qualification remains open.

## The experience we want

A user should be able to describe the task, prepare a brief from permitted source, and copy it into an existing assistant chat. The primary screen should make three things clear: what the app does, what source it uses, and the next useful action. Task type and optional model controls belong in **Options**; ordinary use must not require opening it. Source review, exports and recent briefs remain available on demand.

Two entry points must serve the same job: a person starting in the GUI, or an assistant delegating through a qualified adapter. The core owns the project permissions, task identity, model policy, status, evidence and pause controls. The GUI explains that state; the adapter requests bounded work. The shared coordinator is implemented for explicit shared mode in 0.4.0.dev4; native clients are tested. SDK 2.3.0 and scoped Codex synthetic handoff/cancellation checks have evidence; broader host qualification and the full guided setup/persistence journey remain pending.

```mermaid
flowchart TD
    U["User starts a job"] --> C["Shared local coordinator"]
    H["Assistant delegates"] --> C
    C --> Q{"Qualified local model?"}
    Q -->|Yes| L["Ollama preparation"]
    Q -->|No| E["Evidence-only preparation"]
    L --> R["Review brief, sources and gaps"]
    E --> R
    R -->|More context needed| C
    R --> S["Approved assistant handoff"]
    S --> F["Assistant judgment and final answer"]
```

The diagram is the target connected workflow. Actual host evidence is limited to the scoped Codex synthetic handoff/cancellation check; broader integration remains unqualified. The current app supports explicit manual copy/export; that does not establish delivery to a host or a completed final answer.

## What the source shows now

| Flow step | Current state | Source observation / design consequence |
| --- | --- | --- |
| 1. Open and understand the app | Partial | The GUI centers a request, approved project and Prepare brief. Options and recent briefs are collapsed; empty result panels and idle Stop are hidden. Real projects are configured through launch arguments in `gui.py::main`; guided source/setup selection is missing. |
| 2. Check this computer/model | Partial | Doctor and inventory checks exist; calibration and device-profile management are planned. The workflow needs a clear next action when no model is installed or qualified. |
| 3. Start a job | Shared core and scoped Codex check verified; broader host qualification pending | Shared-mode adapter clients connect through private scoped RPC to the GUI Controller, sharing one routed HelperSession, job registry and session pause. Explicit standalone diagnostics remain separate. See shared-coordinator.md. |
| 4. Prepare and monitor | Implemented contracts; selected browser flows checked | The GUI polls actual status and offers cancellation; the core bounds jobs. A human-readable stage/status contract must cover both entry points. |
| 5. Review a brief | Implemented data views; workflow risks remain | Exact excerpts, hashes, gaps and unverified model notes are shown. `app.js::startTask` retains the previous result; failed/cancelled `showResult` returns before replacing it. The interface now pins completed request/job identity and labels an earlier brief during a new or failed/cancelled job. Selected installed identity, selection and late-copy flows are checked; broader user testing remains pending. |
| 6. Handoff to the assistant | Manual recovery checked; simplified presentation awaiting its own walkthrough | The result offers Copy brief and fixed Claude/ChatGPT links, with exact text and text-file/JSON exports under Review & export; see assistant-handoff.md. Receiving-assistant instructions and job-bound copy feedback are preserved. Earlier installed native/manual transfer, SDK and scoped Codex delivery have evidence; broader host qualification remains open. Copy success is not host delivery or final-task completion. |
| 7. Return, retry or restart | Partial | Question drafts use browser localStorage. History and captured evidence remain session-only. The normal GUI now persists Local AI on/off in private service state and a new installation starts off; session-only Controllers are explicit test/SDK diagnostics. Users need explicit retention/reset information and a deliberate persistent-settings design. |

Useful foundations already exist: job-first task choices; exact source kept alongside notes; published model statistics separated from local records; no candidate silently treated as a qualified winner; and an evidence-only path when model preparation is unavailable. These controls need one understandable path through them.

## Target journey, step by step

1. **First visit: Try a demo or Set up this PC.** The demo teaches the handoff without needing a download. Clearly distinguish recorded preview, live synthetic demo and a real-source job. Returning users can start a job directly.
2. **Readiness: one problem and one action at a time.** Show source permissions, local service, installed models and measured/unknown capabilities. Missing optional AI should leave evidence-only preparation usable. Unsupported platforms and unavailable required source need an explicit explanation.
3. **Compose: describe the task and confirm the source.** Show a concrete question, an approved project and Prepare brief. Keep task type and optional AI under Options, preserving saved choices. Task type selects a model profile but does not alter deterministic collection. Reveal unavailable saved choices or trial acknowledgement controls when they need attention. The handoff uses the user's existing assistant chat; no destination selector is needed.
4. **Prepare: report actual stages.** Use plain states such as Checking source, Gathering evidence and Organizing locally, derived from backend events. Show actual completed counts when available; no invented percentage or ETA. Stop/cancel must describe whether only the client/owned runner stopped and what remains unknown about the daemon.
5. **Inspect: a compact brief with expandable proof.** Pin the original request, job ID, task category and captured source identity. Make facts, model interpretation, contradictions and missing context distinct. A preparation result is labeled Brief prepared or Evidence gathered; it is not Bug fixed or Final answer ready.
6. **Handoff: show what will leave the PC.** Keep manual Copy brief honest about the next paste step. Future connected Send controls require a qualified destination and a source/scope preview. Mark delivery only from an actual acknowledgement. Private-source handling must meet its own security gate.
7. **Continue: ask for more evidence or review the host result.** Preserve the original request and captured brief. A follow-up creates a new linked job/source check when needed. Final answer received requires a real host result or an explicit user record, not a copied clipboard.
8. **Return safely.** Show what was saved, what expires and what needs rechecking. A stale source/model/runtime profile cannot look current. Resume is offered only where durable recovery exists; otherwise preserve the request and offer a clearly new run. The service now remembers AI off; saving/clearing private drafts and durable job recovery still need explicit controls.

## One coordinator and one state contract

Shared-mode GUI and native adapter clients now use one authenticated local controller with the same admission and model-policy rules. SDK and scoped Codex synthetic checks passed; other hosts and broader lifecycle behavior still require qualification. Preserve the existing approved-project-ID boundary and give each client only the fields/permissions it needs. Do not expose the service publicly to solve the UI integration problem.

Each job should carry: job/request identity, source scope/snapshot, preparation mode/profile identity, stage, terminal outcome, evidence/gaps, usage origin and handoff status. Separate a new editable draft from the last completed result. Changes to a draft do not rewrite a previous receipt or silently change the model explanation for that receipt.

The local-AI pause control should have a defined product-wide scope within this service, including assistant-originated jobs, and show acknowledgement. It does not control unrelated services or attest that Ollama stopped GPU work. Persistent preferences, source permissions and qualification records must have explicit versioning and restart behavior. Shared jobs and session pause are implemented in shared mode; Local AI persistence is implemented; other settings, durable jobs and the full restart experience remain planned.

## Failure and empty states

| Situation | Required user-facing state and next action |
| --- | --- |
| No installed or qualified model | Say what was checked and why no model ran. Offer evidence-only preparation or the guided local-model trial/setup path. Never invent a winner. |
| Missing permission or unusable source | Identify the permitted source problem and offer a source choice/scope correction. Keep unrelated host files outside the task. |
| Partial evidence or contradictory code | Show what was collected and missing. Offer a targeted follow-up; do not certify repository-wide completeness. |
| Local model timeout or identity change | Retain exact evidence, show the failed attempt and explain the next check. No silent substitute or retry loop. |
| Busy/expired/disconnected request | Translate the condition into a concrete action. Keep the last completed result clearly labeled and let the user reopen actual job status where retained. |
| Host not connected | Offer manual copy/export as such; keep Final answer pending. |
| New draft while an older result exists | Display both identities clearly; copy/export always names its completed job. A failed new task must not make the older brief appear to be its result. |
| Restart or expired session | Explain which preferences, drafts, jobs and evidence survived. Do not imply recovery where only a browser draft was saved. |

## Visuals that explain the work

Keep the vivid task cards and evidence map. Add one consistent job-stage strip, source/model/handoff status cards and expandable details rather than several competing success badges. Color is accompanied by text; unknown values are labeled. Animation represents a real stage or a labeled conceptual diagram, never an invented measurement.

Model details have separate This PC, Publisher results, Why selected and License & source sections. Comparison charts require comparable measured cohorts, settings, units and dates; otherwise show the reason a comparison is unavailable. The main task view stays compact while source receipts, hardware/runtime, hashes and advanced controls remain available on demand.

## First implementation slices

1. **Shared job/policy/pause semantics:** design the local service contract and qualified adapter bridge; prove both entry points observe the same job and permissions.
2. **Guided first useful run:** demo, approved source selection, readiness checks and a clear unqualified-model path without hand-editing policy files as the normal beginner flow.
3. **Pinned result and recovery states:** separate drafts/active jobs/completed briefs; use actionable errors and explicit retention/restart behavior.
4. **Honest handoff:** preview/copy first, then actual qualified host delivery and acknowledgement; preserve evidence and gaps.
5. **Calibration and detail views:** add the planned hardware/profile/license views using actual backend records, followed by desktop/phone and accessibility review.

These are product/engineering priorities in parallel with the accuracy trial. The first shared-core slice plus first-run help and result identity are now implemented; the remaining guided setup, persistent profiles and actual host-delivery UI are still planned. The source launcher and saved Local AI choice are now implemented; see validation-0.4.0.dev7.md.

## Task-based acceptance checks

- [ ] A first-time user can complete the inert demo and explain what the helper did and what still requires the assistant.
- [ ] A returning user can pick an approved project/job without losing the prior result or unknowingly using an old brief.
- [ ] A user can tell whether Ollama actually ran, why a profile was selected or rejected, and what evidence remains missing.
- [ ] GUI and qualified adapter actions use matching job state, model gates, permissions and pause behavior.
- [ ] Missing models, busy service, timeouts, cancellation and stale profiles each provide a specific next action and preserve useful evidence.
- [ ] Before a connected handoff, the user can understand what leaves the PC; copied, delivered and answered states remain distinct.
- [ ] Draft/history/settings retention and restart behavior are understandable and match actual storage/permissions.
- [ ] Desktop/phone, keyboard, focus, disclosures, reduced motion, status announcements and copy/export are tested in the actual app.
- [ ] Observations from real task walkthroughs are recorded; program tests and attractive visuals alone do not close UX-01 or UI-01.
