# Your first useful brief

Shake & Bake gathers exact source excerpts for a question you want to take to
Claude or ChatGPT. The result is a brief to review and paste into your existing
chat. Preparing a brief does not change the project, run its tests or complete
the assistant's answer.

## 1. Open the workbench

On Linux, open a terminal in the Shake-Bake-LLM project folder and run:

```bash
./scripts/run-workbench
```

The launcher chooses an installed Python 3.11 or newer and opens the local app.
No model installation is needed. A new installation starts with Local AI off;
an existing installation retains its saved choice under **Options**. Leave it
off for this first run.

If the browser does not open, use the local address printed in the terminal.
Keep that terminal running while using the app. To stop it, press **Ctrl+C**
there. Opening the HTML page file by itself shows a launch guide.

## 2. Try the synthetic demo

Choose **Synthetic demo** and enter:

> Check whether the validator accepts fewer slices than expected.

Select **Prepare brief**. When it finishes, open **View source excerpts** to
inspect what was collected. Read any **Gaps & collection limits** before sharing.
Selected excerpts can miss relevant context, so the receiving assistant may need
more source.

Select **Copy brief**, then paste and send it in your Claude or ChatGPT chat.
**Review & export** shows the exact handoff and offers a text file and manual
copying if clipboard access is unavailable. The app does not send it for you.

## 3. Add a project deliberately

Stop the app and launch it with a project name and an absolute folder path:

```bash
./scripts/run-workbench --project my-project=/absolute/path/to/project
```

Replace the example path with the folder you intend to inspect. For a path with
spaces, quote the entire argument:

```bash
./scripts/run-workbench --project 'my-project=/absolute/path/with spaces/project'
```

Choose **my-project** in the app. Ask a concrete question, such as “Find where
failed sign-ins are handled and show the retry limits.” Review the excerpts
before copying them: ordinary source files can contain private information.
Filename exclusions do not guarantee secret detection.

## What stays saved

- **Task draft:** browser storage by default. Under **Options → Task draft**,
  turn off **Save this task draft in this browser** to remove the saved draft while
  keeping the current page's text. **Clear draft** removes the request from the
  page and its saved draft; it leaves the captured brief available.
- **Recent briefs and captured source:** only the running service session,
  bounded to eight jobs and approximately five minutes. Save an export you need
  before restarting or leaving the page. A browser draft does not restore a job.
- **Local AI on/off:** private local service settings across restarts. Models,
  reviewed profiles and automatic calibration are separate; a successful demo
  does not qualify a model.

## If something interrupts you

| What you see | Next action |
| --- | --- |
| Local session unavailable | Check the terminal, then use **Retry connection**. |
| Preparation start not confirmed | Check **Recent briefs** before starting again; the service may already have accepted it. |
| Saved project unavailable | Explicitly choose an approved project for the restored draft. |
| Clipboard unavailable | Open **Review & export**, select the text or save it as a `.txt` file. |
| Port unavailable | Relaunch with `--port 8422` and use the newly printed address. |
| Preferences already in use | Return to the running instance. A separate diagnostic instance needs its own private `--state-dir` and port. |

For deliberate model trials and owner-PC checks, continue with the
[PC checklist](PC-CHECKLIST.md). For the measured limits of the current
development preview, see [evaluation status](evaluation-status.md).
