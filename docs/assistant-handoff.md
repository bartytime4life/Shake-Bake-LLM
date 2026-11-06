# Continue in Claude or ChatGPT

The workbench prepares a brief; the assistant continues the task after you share it.

1. Choose an approved project, describe the task and select **Prepare for my assistant**. Review the exact excerpts and gaps.
2. In **Continue in your assistant**, choose **Claude** or **ChatGPT**. Expand **Review or copy brief text** to inspect the text, then select **Copy brief**.
3. Select **Open Claude** or **Open ChatGPT**, choose a chat, paste the brief into the message box, review it and send it. You can also paste into the assistant's desktop app.

If copying is unavailable, expand **Review or copy brief text**, select **Select all text**, then use your device's Copy command. **Save brief as .txt** saves the same text for attachment where uploads are available. Prepare a narrower request if a brief exceeds the destination's limits. **Long brief or need the full record?** contains the JSON export.

The brief includes the unchanged original request, exact source, gaps, unverified model notes and instructions for the receiving assistant. It asks for supported conclusions, path/line citations and explicit uncertainty. The source and request remain JSON-encoded to preserve their exact values, including line endings. Copy, text save and JSON export use the captured result, even while the task above is edited or another task is running.

Choosing an assistant only changes a fixed public website link and the paste instructions. The selected destination is page-local and resets on reload. The link carries no source, request, task identifier or prompt query. It opens a separate tab without an opener or referrer. Nothing is sent automatically. Copy completion does not establish delivery, a final answer or changes to local files. A cloud chat receives only what the user pastes or attaches; it does not gain access to the inspected project. Connected native-host qualification remains separate.

Official references checked November 5, 2026: [ChatGPT project context and pasted text](https://help.openai.com/en/articles/10169521-projects-in-chatgpt), [Claude file uploads](https://support.claude.com/en/articles/8241126-upload-files-to-claude). Available upload types, limits and account features belong to the destination service.

## Scoped development evidence

The current-screen walkthrough found two points of friction: completed results exposed only Copy brief/Download JSON, with no destination or paste step; the text export contained evidence but no clear instructions for the receiving assistant. The change adds a three-step handoff, a labeled assistant selector, a prominent copy action, a text-file alternative and receiving-assistant guidance using the existing workbench styling. Advanced JSON export remains available.

- All 177 Python tests pass with Python 3.14.4. Frontend syntax/API smoke, 30 readiness VM cases, 15 clipboard/handoff VM cases, 6 request-deadline cases, 3 file-launch cases and 4 server-startup cases pass. New cases check fixed destinations without transmission, identical preview/copy/text-file content, exact CR/CRLF and hostile-string preservation, and captured-job identity after draft/history changes.
- An offline isolated wheel build with Python 3.12.3 passes inspection. All 33 installed runtime/asset files match source. Installed shared-job/preference-restart smoke, 177 Python tests and the relevant VM suites pass.
- An isolated in-app-browser session with Local AI off completed the synthetic demo. Both assistant choices updated their fixed links and paste steps. Manual selection/keyboard copy and the saved text file each matched the 4,193-character displayed brief exactly. The browser reported Copy brief success, but the automation virtual clipboard returned empty and could not paste it; this is retained as a tool-path limitation, not claimed as a successful native clipboard readback. A separate native clipboard browser regression runs in CI.
- Desktop and 390-pixel responsive checks showed the handoff controls and no page-wide horizontal overflow. Keyboard focus advanced from Assistant to Copy brief to the assistant link. No warning/error console entries were observed. Before/after screenshots are retained locally outside the repository. This is selected-flow evidence, not formal accessibility or wider-device qualification.
- The existing CI browser runner gains a synthetic handoff case for both destinations, exact text-file download, native clipboard content, an unchanged captured result after editing the draft, mobile overflow and no external requests from selection/copy/save. Hosted results are reported by CI, separately from the local walkthrough.

No brief was submitted to Claude or ChatGPT during this check. Actual assistant answers, automated delivery, private-source handling and broader host integration remain unqualified.
