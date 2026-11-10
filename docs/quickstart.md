# Check a failed run

Open a terminal in this project on Linux and run:

```bash
./scripts/run-workbench
```

Keep that terminal open. The launcher chooses Python 3.11 or newer and opens the local app. No model installation is needed.

1. Open **Connect project folder** above either workflow. Enter the absolute folder path containing the failing code, then select **Connect folder**. The name is optional. Connection approves read-only inspection for this service session.
2. Paste the complete error output, or select **Load error file** for a UTF-8 `.txt` or `.log` up to 64 KiB. Loading alone makes no service request. Optionally record the command that failed. The app never runs that command.
   If you ran it in a project subfolder, enter that folder in **Folder where the command ran**. Blank uses the connected root; a relative folder such as `services/api` stays inside that root. The recorded command never chooses the folder for you.
3. Select **Find failing source**. Inspect the highlighted line and whether it matches the statement in the traceback. A mismatch can mean the error came from a different source version.
4. Read the suggested next checks and limits. Select **Copy debugging brief** for your AI chat, or save the text/JSON report if you need it after closing the page. If copying fails, select the exact handoff text shown on the page. Review any possible-credential warning before sharing. Nothing is sent automatically.

Python tracebacks, complete default/long or short pytest failure reports, Node.js V8 stacks and TypeScript compiler diagnostics are supported. For several pytest failures, the main result uses the final test section; other captured tests are in matching details. A source location shows where to investigate; it does not establish the cause or verify a fix. A missing file, unsupported log or outside-project frame is reported explicitly. Editing the error, command or selected project makes the previous result outdated; rerun the check before copying or exporting. The bundled **Try a labelled example** is synthetic and optional.

For a repository question, choose **Prepare source brief**. You can connect its folder from the same shared control; a successful connection selects it for the workflow you used. The other workflow's selection and inputs stay unchanged. Ask a specific question, inspect the source excerpts, then copy the brief into your existing AI chat. A brief with no source cannot be copied as a successful handoff. The receiving assistant supplies the final reasoning.

## What stays saved

- Pasted errors, recorded commands and failure reports stay in the open tab and are not saved in browser storage or sent to a model. Exports contain the exact error and source; review them before sharing.
- Connected folders last until the service stops. Reconnect after restarting, or use the launch option `--project 'my-project=/absolute/path/to/project'`.
- Source-brief task drafts save in this browser by default. Under **Options → Task draft**, turn off saving or use **Clear draft**. This setting does not save pasted failures.
- Recent source briefs last only in the running service, up to eight jobs and approximately five minutes. Save any export you need.
- Local AI on/off persists in private service settings. The failed-run workflow does not use Local AI.

If the session disconnects, check the terminal and select **Retry connection**. After a same-address restart, Retry renews the browser session without reloading or repeating a task. Error text, the recorded command, the working folder and captured reports stay in the open tab. Session-only folder approvals and service jobs expire: reconnect any missing project and check again. Retained reports describe their earlier capture. Closing or reloading the tab still discards failure text and reports. For a port conflict, relaunch with `--port 8422` and use the printed address. Stop the app with **Ctrl+C** in its terminal.
