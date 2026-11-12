# Visual workbench

Current guidance for `0.4.0.dev37`. [Current status](current-status.md) records the source, validation and delivery state. The [dev36 workbench review](workbench-usability-2026-11-11.md) and [dev37 capture-recovery record](captured-report-recovery-2026-11-11.md) retain dated checks, screenshots and qualification limits.

The standalone workbench offers two jobs: **Diagnose a failed run** and **Prepare source brief**. It uses the recovered application's controller and bounded child, Python's standard library and bundled HTML/CSS/JavaScript/SVG. No external frontend service, fonts, icon service or business application is required. Exact source stays separate from optional, unverified model notes.

## Open and prepare

```bash
./scripts/run-workbench
```

The launcher selects an installed Python 3.11 or newer. Neither workflow needs a model. Add owner-approved folders at launch with `--project my-project=/absolute/folder`, or explicitly connect a folder for the running session. **Connect folder** beside either project selector opens the shared **Connect project folder** form and focuses its absolute-path field. A successful connection selects the folder only for the workflow that requested it. Models cannot approve folders. Up to eight projects include the demo. `--policy /absolute/owner-policy.json` must remain outside source roots; `--no-browser` and `--port 8422` are available. An installed wheel provides `shake-bake-ui`.

Open the local address printed by the launcher. Opening `src/shake_bake/web/index.html` directly shows a launch guide and does not connect, save drafts or prepare source; the separate recorded export remains inspectable offline. See [file-opening recovery](file-launch-recovery-2026-11-05.md).

For an error, paste complete output or select **Load error file**. Choose its project and select **Find failing source**. **Run details (optional)** holds the recorded command and working folder; closing it keeps their values. Read the source, **What to check next**, missing locations and cutoff notices. Other frames and explicit error associations are under **Error locations & matching details**; general limitations are under **Source-check boundaries**. No command, model call, diagnosis or fix is performed by this check. See the [quickstart](quickstart.md).

The last accepted failed-run report stays visible during a recheck and after failure or an obsolete response. A notice identifies the earlier capture; it is not refreshed until a valid current response replaces it. Copy, text export and manual-copy review wait while a check is pending or inputs differ. **Original error & report → Download captured JSON report** saves the displayed capture even then, without newer draft edits. Its credential warning remains attached to that capture. After a failed same-input recheck, the earlier report can be copied again with the notice that it was not refreshed. A successful replacement supersedes it; save required JSON first.

For a source question, choose **Prepare source brief**, enter the request, choose its project and select **Prepare brief**. Ordinary evidence-only use needs no Options. Task type and optional model controls remain in **Options**. Exact excerpts, line ranges and hashes are available with the original request, job identity, route explanation and receipt. Documents means supported text files; PDF/image extraction and explicit range selection are not provided by this GUI. Bounded lexical selection can omit relevant source.

**Copy brief** uses the selected **Brief layout**: **Starting points (default)** gives orientation and short selected excerpts; **Full evidence, cited answer** includes every captured excerpt. **Review & export** contains selectable text, **Save brief as .txt** and **Download JSON record**. Source-brief exports remain tied to the pinned result while the task draft is edited or another task runs or fails. The JSON retains the full native result, exact request/source, evidence identities and hashes. Clipboard and chat clients may normalize line endings; use JSON and hashes when byte identity matters. See [the handoff guide](assistant-handoff.md).

Pending/completed copy feedback identifies the exact copied job and text. Changing layouts can identify an earlier layout; returning to the same bytes restores that identity. One unsettled clipboard write blocks another in either workflow in this tab. Manual clipboard actions and other tabs are outside this guard. Fixed Claude/ChatGPT links open the service only: copy, paste and send remain explicit user actions, and copy success is not proof of delivery or an answer.

A shared activity notice follows source preparation across workflows. **View preparation** returns to its actual starting/running/unknown status and existing **Stop** action. A conflicting failed-run check waits, while its inputs remain editable. There is no invented progress percentage or ETA.

## Local AI modes

Local AI off disables new model use and cancels this controller's owned active runner. It does not stop the separate Ollama daemon or attest GPU cancellation. Off also prevents inventory requests. Best tested selects only eligible owner-record profiles on comparable reviewed trials; the shipped candidates do not qualify. Model availability and reported digest are checked on use. No model is downloaded and no cloud-provider fallback exists.

For an explicit diagnostic candidate trial:

```bash
PYTHONPATH=src python3 -B -m shake_bake gui --allow-candidate-trials
```

In **Options → Model details**, select **Refresh installed models**, choose **Try a candidate — unqualified**, select an installed model and acknowledge unverified notes and the trusted cloud-disabled daemon requirement. Preparation mode stays disabled until the initial session and saved choices are ready, during unconfirmed settings, or while disconnected. The launch flag, enabled owner policy, acknowledgement and pinned digest are enforced outside the model. Native tools cannot select candidates or alter policy. A trial cannot promote a profile. Failures discard notes while retaining captured source; full task cancellation produces no new completed result.

Candidate notes remain separate from source. Structured-output/reference checks do not establish correctness. The client requests `think: false` and `keep_alive: 0`; returned thinking/tool output is refused. The daemon remains separately trusted. Published catalog statistics retain their source links and a distinct statement that no local qualification is inferred.

## State and boundaries

A browser request that stalls for 15 seconds reports a timeout; browser suspension can delay this timer. Unknown preparation status can still keep conflicting work waiting. If a task start was not confirmed, the service may still have accepted it. The app checks session state, resumes monitoring any retained running job and asks you to check **Recent briefs** before starting again. It never automatically repeats a start. Explicit **Retry connection** can renew an expired same-address session without reloading or replaying work. Open-tab inputs and captures remain, but missing folder approvals must be explicitly restored. Save required captures before reloading or closing. See [request recovery](request-recovery-2026-11-05.md) and [session and capture recovery](captured-report-recovery-2026-11-11.md).

Once connected, task controls and **Recent briefs** remain available while a retained brief loads. History distinguishes failed preparations, incomplete empty results and prepared captures. Startup selects the latest prepared/incomplete result, skipping newer failures and preserving the draft. Older metadata without outcome/evidence facts is labelled completed and remains manually reviewable without a prepared claim. Automatic restoration cannot replace a newer selected or prepared result, or overwrite its feedback with an old error. See [startup restoration](startup-brief-recovery-2026-11-05.md) and [dev37 recovery](captured-report-recovery-2026-11-11.md).

The browser can remember the request draft, project and task type in localStorage; mode and candidate identity are separate preferences. Captured source is not persisted there. **Options → Task draft** provides saving opt-out and **Clear draft**; neither erases an accepted capture, clipboard contents or downloaded files. Failed-run inputs and their one accepted report remain only in the open tab. The Local AI checkbox follows the running controller's pause/policy state. The normal GUI persists Local AI on/off in private service state and new installations start off; up to eight source jobs with approximately five-minute retention remain session-only. Explicit test/SDK Controllers can use session-only preferences; see [preference boundaries](local-ai-preferences.md). There is no durable job recovery. Restart invalidates old task handles and session-only folder approvals; launch grants and model policy remain owner configuration.

The saved request restores with its own project and task type, even if separate preferences differ. If either saved choice is unavailable, select an approved replacement before preparation; the request remains visible. Edits made while the first connection is pending are retained. Saving status appears below the request: if browser storage fails, keep the page open or copy the task text before leaving. Draft saving is scoped to the browser origin, including port. Opt-out changes propagate across tabs, but concurrent task editing is not synchronized and a saved project ID does not attest a remapped root's identity. See [draft controls](draft-privacy.md) and the dated [draft recovery checks](draft-context-2026-11-05.md).

The numeric-loopback service uses an HttpOnly SameSite cookie, Host/Origin/CSRF checks, a fixed asset allowlist and bounded request/connection handling. It is a trusted local owner session, not multi-user isolation or a public service. `--connection-file` publishes a private shared-adapter capability outside source; each host needs separate qualification. See [shared coordinator](shared-coordinator.md).

`tools/export_preview.py` captures only the bundled inert demo into self-contained HTML. It embeds local assets, marks the recorded state, refuses new jobs/model operations and permits inspecting/copying that recorded evidence. It is distinct from the live application.

Current results are indexed in [evaluation status](evaluation-status.md), including [readiness checks](pc-readiness-2026-11-05.md) and [copy recovery](copy-and-screening-2026-11-05.md). The earlier [validation](validation-0.4.0.dev6.md) and [design QA](../design-qa.md) retain their dated scope. The archive import record remains historical and unchanged. Formal accessibility, wider devices, independent security, held-out accuracy, actual native-host UX and savings remain open.

## Historical design context

The owner selected the third proposed design in November 2026: graphite surfaces, amber actions, a project/history rail, broad task composer and paired exact-source panels. The earlier dev8 guide described that layout. The dev36 simplification retains the visual palette while changing the current entry, navigation and disclosure placement. The dated [design QA](../design-qa.md) and [dev36 observations](workbench-usability-2026-11-11.md) describe their tested versions; neither is universal accessibility or usability qualification.

## Explicit readiness checks

Inside Model details, expand This computer & selected model. Check this computer reads bounded local CPU/memory/GPU metadata without commands or network; it works with Local AI off. Check selected model reads the pinned candidate digest, Ollama version, quantization, context and capabilities without source or generation. It requires Local AI on; changing selection clears the old check. Values identify their observation origin/time and leave unknowns explicit. They do not qualify accuracy or prove memory fit. Full automatic tuning, installation identity and persisted qualified profiles remain planned.
