# Prepare for ChatGPT or Claude

Current guidance for `0.4.0.dev38`. See [current status](current-status.md) for source, validation and delivery state; the [dev36 workbench review](workbench-usability-2026-11-11.md) and [dev37 recovery checks](captured-report-recovery-2026-11-11.md) retain their own evidence and limits.

Open a terminal in this project on Linux and run:

```bash
./scripts/run-workbench
```

Keep that terminal open. The launcher chooses Python 3.11 or newer and opens the local app. No model installation is needed.

The app opens **Prepare source brief**. Connect the project folder, describe your task, then use the visible **Local AI — Ollama junior developer** control and **Model details** for local-model preparation. No model profile is currently qualified for **Best tested**. To try an installed model explicitly, launch with `--allow-candidate-trials`, enable Local AI, choose **Try a candidate — unqualified**, refresh models, select one and acknowledge the trial. Use a trusted local Ollama daemon with cloud features disabled. No automatic download or cloud call occurs.

Select **Prepare brief**, review the junior developer draft, exact source and gaps, then **Copy brief** and paste it into **ChatGPT or Claude as the main developer**. That assistant reviews the draft and decides the solution and verification. Local AI off or an unavailable/unqualified draft leaves a labelled evidence-only handoff. See [the complete handoff guide](assistant-handoff.md) and [product purpose](product-purpose.md). Whole-task token and financial savings are not yet established.

## Gather evidence for a failed run

1. In **Diagnose a failed run**, select **Connect folder** beside **Project containing the failing code**. This opens the shared **Connect project folder** form. Enter the absolute folder path containing the failing code, then select its **Connect folder** button. The name is optional. Connection approves read-only inspection for this service session.
2. Paste the complete error output, or select **Load error file** for a UTF-8 `.txt` or `.log` up to 64 KiB. Loading alone makes no service request. **Error formats & privacy** explains the supported input and storage boundaries.
   Open **Run details (optional)** to record the command that failed or **Folder where the command ran**. The app never runs the command. Blank working-folder text uses the connected root; a relative folder such as `services/api` stays inside that root. The recorded command never chooses the folder for you. Closing this disclosure keeps its values.
3. Select **Find failing source**. Inspect the highlighted line and whether it matches the statement in the traceback. A mismatch can mean the error came from a different source version.
4. Read **What to check next**, visible missing locations and limits. **Error locations & matching details** contains other frames and explicit error associations; **Source-check boundaries** contains general limitations. Select **Copy debugging brief** for your AI chat. If copying fails, use **Review debugging brief or copy manually**. Under **Original error & report**, **Save report as .txt** saves the debugging handoff and **Download captured JSON report** preserves the complete displayed capture. Review any possible-credential warning before sharing. Nothing is sent automatically.

Python tracebacks, complete default/long or short pytest failure reports, Node.js V8 stacks and TypeScript compiler diagnostics are supported. For several pytest failures, the main result uses the final test section; other captured tests are in matching details. Supported Node.js aggregate members retain their own error associations; unsupported nested structures remain incomplete. A source location shows where to investigate; it does not establish the cause or verify a fix. A missing file, unsupported log or outside-project frame is reported explicitly. The bundled **Try a labelled example** is synthetic and optional.

Editing the error, command, working folder or selected project makes the displayed report an earlier capture. Copy, text export and manual-copy review wait for a check of the current inputs. The last accepted report remains visible through a pending, failed or obsolete recheck, and **Download captured JSON report** stays available; it saves that capture, without newer edits. After a failed same-input recheck, copying the earlier capture becomes available with an explicit notice that it was not refreshed. A valid replacement supersedes the previous report, so save any JSON you need before checking again.

For a repository question, choose **Prepare source brief**. Select **Connect folder** beside **Project** if needed; a successful connection selects it for the workflow you used. The other workflow's selection and inputs stay unchanged. Ask a specific question, select **Prepare brief**, inspect the source and gaps, then **Copy brief** into your existing AI chat. **Brief layout** defaults to **Starting points (default)**; **Full evidence, cited answer** includes every captured excerpt. **Review & export** provides manual copy and text/JSON saves. A brief with no source cannot be copied as a successful handoff. The receiving assistant supplies the final reasoning.

A shared activity notice keeps source preparation visible when you switch workflows. **View preparation** returns to its status and existing **Stop** action. A conflicting failed-run check waits while preparation is pending, running or its status is unknown; you can still edit your inputs. Stop concerns the owned preparation runner, not proof that a separate model daemon stopped all work.

## What stays saved

- Pasted errors, recorded commands and failure reports stay in the open tab and are not saved in browser storage or sent to a model. Exports contain the exact error and source; review them before sharing.
- Connected folders last until the service stops. Reconnect after restarting, or use the launch option `--project 'my-project=/absolute/path/to/project'`.
- Source-brief task drafts save in this browser by default. Under **Options → Task draft**, turn off saving or use **Clear draft**. This setting does not save pasted failures.
- **Recent briefs** lasts only in the running service, up to eight jobs and approximately five minutes. History distinguishes failed preparations, incomplete empty results and prepared captures. Startup can restore an earlier prepared/incomplete result after a newer failure without changing the draft or repeating a task. Older metadata may say completed without claiming prepared evidence. Save any export you need.
- Local AI on/off persists in private service settings. The failed-run workflow does not use Local AI.

If the session disconnects, check the terminal and select **Retry connection**. After a same-address restart, Retry renews the browser session without reloading or repeating a task. Error text, the recorded command, the working folder and captured reports stay in the open tab. Session-only folder approvals and service jobs expire: reconnect any missing project and check again. Retained reports describe their earlier capture. Closing or reloading the tab still discards failure text and reports. For a port conflict, relaunch with `--port 8422` and use the printed address. Stop the app with **Ctrl+C** in its terminal.
