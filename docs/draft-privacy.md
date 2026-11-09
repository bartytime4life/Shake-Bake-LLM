# Control browser task drafts

In **Options → Task draft**, **Save this task draft in this browser** controls whether the workbench remembers the current request, project and task type in browser storage. Saving remains on by default for existing users.

- Turning saving off removes the stored task draft, keeps the current text and choices on the page, and preserves any prepared brief. The off choice survives a reload on the same browser origin. New task edits are not stored while it is off.
- Turning saving on saves the current nonempty task once the local session has connected. The choice must be saved successfully before task text is written.
- **Clear draft** empties the current request and removes its saved draft. It keeps the project, task type, model choices and prepared brief, then returns keyboard focus to the request. An empty task does not create a replacement storage record.
- An opt-out in another tab updates an open tab without erasing its current text. Each task write checks the saved choice before and after writing, so a delayed browser storage event or an opt-out during the write cannot leave a saved draft. Clearing browser storage in another tab leaves existing pages off until saving is explicitly enabled again.
- A page opened after an opt-out ignores and retries removal of an older saved task, including a draft left behind by a failed earlier removal. Storage failures remain visible beside the request. If the browser cannot confirm the saved preference or removal, the page says so and keeps new task text out of storage in that page.

These controls manage the task draft for the current browser origin. Changing the browser, profile or local port uses a different storage area. Removing all browser storage resets the saved preference for newly opened pages. Other interface preferences remain separate.

Clearing a draft does not erase a task already submitted to the running service, a prepared brief, copied text or downloaded files. Completed jobs remain subject to the existing session limits. The controls are disabled in the recorded preview, which never saves drafts, and the file launch guide does not access browser storage.

## Verification boundaries

The workbench browser suite uses the bundled inert synthetic source, an isolated browser context and injected transport/storage failures. It checks opt-out and re-enable behavior, reload, unavailable saved context, exact task text, unchanged prepared exports, early interaction during connection, cross-tab events and delayed events, external storage clearing, failed preference writes and removals, clear-draft keyboard focus, empty-record prevention, responsive page width and inert previews. These checks do not qualify all browsers, assistive technologies, actual models or private-source workflows.

On November 9, 2026, all 41 workbench scenarios passed on the local PC using Python 3.12 and Chrome 157. The file-launch, clipboard and model-readiness JavaScript checks also passed (3, 16 and 30 checks respectively). Desktop and phone layouts were inspected; a full screen-reader or formal accessibility audit remains open.

The source viewer also splits CR-only, CRLF and the Unicode line boundaries recognized by the Python collector. Numbered display rows now agree with captured line ranges; the original captured source remains unchanged in the handoff and JSON export. A synthetic response regression checks all supported boundaries and exact exported text.

The ready-result area also explains that session history is temporary and points
to **Review & export** to save a copy. This reminder does not imply durable job
recovery or change the captured brief.
