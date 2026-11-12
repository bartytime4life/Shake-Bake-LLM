# Continue in Claude or ChatGPT

Current guidance for `0.4.0.dev37`. See [current status](current-status.md) for source, validation and delivery state. The [dev36 workbench review](workbench-usability-2026-11-11.md) and [dev37 capture-recovery record](captured-report-recovery-2026-11-11.md) retain dated evidence; the earlier follow-ups below describe their own versions.

The workbench prepares captured evidence. The receiving assistant continues the task after you explicitly share it.

1. Choose **Prepare source brief**, describe what you need, select a project and select **Prepare brief**. **Connect folder** beside **Project** opens the shared connection form if needed. No model or Options changes are required for ordinary evidence-only preparation.
2. Review the captured request, source and any **Gaps & collection limits**. Use **View source excerpts** for the captured records. Select a **Brief layout**, then **Copy brief**.
3. Paste into your Claude or ChatGPT chat and send. The assistant links are shortcuts; an already-open chat or desktop app works too. Review any possible-credential warning before sharing.

**Review & export** contains selectable handoff text, **Select all text**, **Save brief as .txt** and **Download JSON record**. If clipboard copying is unavailable, open the disclosure and use your device's Copy command or the text save. The text file uses the selected layout. Prepare a narrower request if the brief exceeds the destination's limits.

## Choose the handoff text

| Brief layout | What the assistant receives |
| --- | --- |
| **Starting points (default)** | A matching-file orientation, short selected source excerpts, scan limits, explicit uncertainty and exact-value verification fields. It asks the assistant to investigate rather than presenting an answer. It does not include every captured excerpt. |
| **Full evidence, cited answer** | Every captured excerpt, available context-map and uncovered-match details, scan limits, and a request for cited findings, uncertainties and any additional source needed. |

Both layouts preserve the original request as a JSON string for verification. The displayed request normalizes line endings; that display does not replace its exact captured value. Optional local-model drafts and notes are labelled unverified and remain separate from source. A disclosed shortened model view does not shorten the captured records. See the dated [orientation-default record](workbench-orientation-2026-11-08.md), [handoff-prompt record](handoff-prompt-2026-11-06.md) and [full-evidence format record](handoff-format-2026-11-07.md).

Source, paths and model output remain untrusted reference data. Markdown fences are longer than embedded backtick runs, so captured source cannot close its block or become handoff instructions. Neither layout authorizes commands or gives an assistant access to other files. Excerpts and orientation are bounded retrieval results, not proof of a complete repository review, tests or repairs.

**Download JSON record** retains all captured request/source values, evidence identities and hashes, regardless of the selected text layout. Clipboard and chat clients may normalize line endings; use JSON and hashes when exact-byte verification matters. The brief-size display uses a bytes/4 token estimate, not a provider count.

## Keep the right capture

Source-brief copy and exports use the pinned result even while the task draft is edited or another task runs or fails. Copy feedback names the captured job and exact text: if you change the layout during a pending or completed copy, feedback can refer to the earlier layout. Returning to identical text restores that identity. An unsettled clipboard write cannot be cancelled or overlapped by another workbench copy in this tab; wait for it to finish or use review/export. Other tabs and manual clipboard actions remain outside this guard.

The shared preparation notice stays visible across workflows. **View preparation** returns to the existing source job and **Stop** action. It does not start a replacement task. A disconnected job has unknown status until reconnected; no progress percentage or ETA is inferred.

For a failed run, **Copy debugging brief** packages the exact captured error, recorded command, project/working-folder identity, source, explicit error/frame/evidence associations, missing locations and suggested checks. **Review debugging brief or copy manually** provides its fallback; **Original error & report** contains the text save and **Download captured JSON report**. A last accepted report remains visible during failed or obsolete rechecks. Copy/text/manual handoff wait while checking or when inputs differ, but its captured JSON remains saveable and excludes newer edits. After a failed same-input check, copying the earlier capture becomes available with a not-refreshed notice. A successful replacement supersedes it. See the [failed-run guide](failed-run-workflow.md).

**Options** contains task type, task-draft controls and optional Local AI. A new installation starts with Local AI off. Candidate trials require the owner's launch permission and explicit acknowledgement; they do not qualify a model. Missing or failed optional model notes do not turn captured evidence into an answer.

## Sharing and retention

The Claude and ChatGPT links are fixed public website links. They carry no source, request, task identifier or prompt query, and open a separate tab without an opener or referrer. Nothing is sent automatically. Copy completion does not establish delivery, a final answer or local-file changes. A cloud chat receives only what you paste or attach; it does not gain access to the inspected project. Connected native-host qualification remains separate.

Failed-run inputs and their accepted report live only in the open tab. Source-task history belongs to the running service, up to eight jobs and approximately five minutes; source drafts and selected preferences use separate browser storage. Save needed captures before replacement, reload, closure or service expiry. **Retry connection** preserves open-tab data without replaying work, but does not restore expired project approvals or make old source current. See [draft privacy](draft-privacy.md).

Destination references last checked November 5, 2026: [ChatGPT project context and pasted text](https://help.openai.com/en/articles/10169521-projects-in-chatgpt), [Claude file uploads](https://support.claude.com/en/articles/8241126-upload-files-to-claude). Upload types, limits and account features belong to the destination service and may change; no current account capability is inferred here.

## Simplification follow-up, November 6, 2026

Owner feedback found the visible settings, empty result panels and handoff tutorial made the simple task feel complicated. The follow-up centers the request and **Prepare brief**, moves technical choices into **Options**, and shows the compact copy result only after preparation. Recent briefs, source review and exports remain available on demand. Idle Stop is hidden. This changes presentation and recovery visibility, not collection, model policy or exact export content.

The browser regressions cover the normal path without opening Options, recovery from an unavailable saved task type, candidate acknowledgement recovery, fixed assistant links, and the existing setting/history/clipboard races. Hosted execution is reported by CI separately from the checks below. Wider accessibility, actual assistant delivery and representative user-task qualification remain open.

All 177 Python tests pass after updating the served-page heading assertion. An isolated synthetic in-app-browser walkthrough completed preparation with Options closed, then verified the ready-heading focus and next Tab to Copy at 390 pixels. Desktop, tablet and phone layouts were inspected; the phone flow had no horizontal overflow. Manual keyboard copy and the text-file download each matched the 4,131-character brief preview exactly. Completion also has a dedicated polite announcement; preserved focus during concurrent draft editing is covered by the browser regression awaiting hosted execution. Screenshots and the downloaded synthetic file remain outside Git. These checks did not submit a brief to an assistant or run a local model.

Local non-browser checks for this follow-up pass: frontend API smoke, 30 readiness VM cases, 16 clipboard/handoff VM cases, 6 request-deadline cases, 3 file-launch cases and 4 server-startup cases. The clipboard checks retain exact request/source and delayed-result assertions, and add idle/active control visibility and manual-copy focus recovery. JavaScript syntax and whitespace checks pass. These checks do not exercise a real browser or OS clipboard.

## Earlier scoped development evidence, November 5, 2026

The current-screen walkthrough found two points of friction: completed results exposed only Copy brief/Download JSON, with no destination or paste step; the text export contained evidence but no clear instructions for the receiving assistant. The change adds a three-step handoff, a labeled assistant selector, a prominent copy action, a text-file alternative and receiving-assistant guidance using the existing workbench styling. Advanced JSON export remains available.

- All 177 Python tests pass with Python 3.14.4. Frontend syntax/API smoke, 30 readiness VM cases, 15 clipboard/handoff VM cases, 6 request-deadline cases, 3 file-launch cases and 4 server-startup cases pass. New cases check fixed destinations without transmission, identical preview/copy/text-file content, exact CR/CRLF and hostile-string preservation, and captured-job identity after draft/history changes.
- An offline isolated wheel build with Python 3.12.3 passes inspection. All 33 installed runtime/asset files match source. Installed shared-job/preference-restart smoke, 177 Python tests and the relevant VM suites pass.
- An isolated in-app-browser session with Local AI off completed the synthetic demo. Both assistant choices updated their fixed links and paste steps. Manual selection/keyboard copy and the saved text file each matched the 4,193-character displayed brief exactly. The browser reported Copy brief success, but the automation virtual clipboard returned empty and could not paste it; this is retained as a tool-path limitation, not claimed as a successful native clipboard readback. A separate native clipboard browser regression runs in CI.
- Desktop and 390-pixel responsive checks showed the handoff controls and no page-wide horizontal overflow. Keyboard focus advanced from Assistant to Copy brief to the assistant link. No warning/error console entries were observed. Before/after screenshots are retained locally outside the repository. This is selected-flow evidence, not formal accessibility or wider-device qualification.
- The existing CI browser runner gains a synthetic handoff case for both destinations, exact text-file download, native clipboard content, an unchanged captured result after editing the draft, mobile overflow and no external requests from selection/copy/save. The first hosted run passed the existing native-copy and clipboard-failure cases, then exposed a fixture-order error: the new empty-session assertion ran after earlier scenarios had populated the shared controller history. The new scenario now runs first, preserving the empty-session assertion. Hosted results are reported by CI, separately from the local walkthrough.

No brief was submitted to Claude or ChatGPT during this check. Actual assistant answers, automated delivery, private-source handling and broader host integration remain unqualified.
