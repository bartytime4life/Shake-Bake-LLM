# Shake & Bake

Check a failed run against the code on your computer, then take a precise debugging brief into your AI chat. The workbench reads approved source folders, preserves the original error and shows the exact lines it found. No model is needed for this workflow.

**Development preview: `0.4.0.dev28`. Linux and Python 3.11+ are required.** Finding a source line is a starting point for debugging; a cause or fix still needs investigation and verification.

## Open the app

```bash
git clone https://github.com/bartytime4life/Shake-Bake-LLM.git
cd Shake-Bake-LLM
./scripts/run-workbench
```

The launcher chooses a supported installed Python and opens `http://127.0.0.1:8421`. Keep its terminal running; stop it with **Ctrl+C**. Opening the HTML file directly shows launch instructions rather than starting the service. No model, package installation or download happens automatically.

## Check an actual failure

1. Open **Connect project folder**, enter the absolute folder path containing the failing code, and select **Connect folder**. This approves read-only inspection for the running session.
2. Paste the complete error output, or select **Load error file** for a saved UTF-8 `.txt` or `.log` up to 64 KiB. Optionally record the command that failed; it is never executed.
3. Select **Find failing source**. Inspect the source, reported line and column, unmatched frames and suggested next checks.
4. Select **Copy debugging brief** to take the captured error, project context and exact source into Claude or ChatGPT. If clipboard access fails, select and copy the provided text manually. Nothing is sent automatically.

| Input | What the app checks |
| --- | --- |
| Python traceback | Exact file/line and whether the displayed statement matches current source. |
| Node.js stack trace | Local V8 stack locations, starting with the first readable project frame. |
| TypeScript compiler output | File, line, column and the corresponding compiler diagnostic. |

ANSI terminal colors are ignored only while recognizing locations; the original output remains unchanged. Browser URLs, runtime internals, outside-project files and missing files remain explicit. Source maps and container-to-local path mapping are not inferred. An unsupported log produces an incomplete result.

Changing the project, error or recorded command invalidates the previous result. A late response cannot silently replace the result for newer input. Pasted errors and commands are not stored as browser drafts or sent to a model.

Loading a file stays in the open tab until **Find failing source**. Original file text and line endings are preserved; editing the error uses the edited text instead. Invalid files leave the current error unchanged. **Connect project folder** is available from either workflow and keeps the other workflow's inputs unchanged.

The optional **Try a labelled example** uses invented errors and bundled inert source. It does not demonstrate a failure on your computer. See [the quickstart](docs/quickstart.md) and [supported formats and limits](docs/failed-run-workflow.md).

## Prepare source for a question

When there is no traceback, choose **Prepare source brief**, select your connected project and ask a concrete question, such as “Where is the retry limit applied after a failed sign-in?” Inspect the collected source before copying the brief into your AI chat. An empty result cannot be copied as a successful source handoff.

Selection is bounded lexical retrieval and may miss important context. Your receiving assistant supplies the final reasoning and may need more source. If that assistant already has full repository tools, direct inspection can be more useful; no general time, token or accuracy improvement is established.

An optional Ollama worker can draft unverified preparation notes for source briefs. It is separate from failed-run checks. New installations start with Local AI off; an existing installation retains its saved choice. No shipped model profile is qualified for automatic selection. Read [model setup and trial boundaries](docs/pc-readiness-and-trials.md), [routing](docs/routing-implementation.md) and [evaluation status](docs/evaluation-status.md) before enabling model trials.

## Local data and scope

- Connected folders and failure reports are session-only. A restart requires reconnecting folders unless supplied at launch. Failure reports also disappear when their tab closes; save an export you need.
- Source-brief drafts save in this browser by default. **Options → Task draft** lets you disable saving or clear a draft. Recent source briefs last up to eight jobs and approximately five minutes in the running service.
- Local AI on/off persists in private service settings. Models, reviewed profiles and durable job recovery are separate.
- Possible credential formats are flagged with masked previews before sharing, including in pasted errors and recorded commands. This warns without changing exact evidence; no match is not proof that content is safe. See [credential screening](docs/credential-screening-2026-11-09.md).
- Exports include the exact error, command and captured source. Review them before sharing. Filename exclusions do not guarantee secret detection.
- Folder approval in the browser does not expand an existing assistant adapter's project scope. The app does not execute inspected code, install dependencies, run tests or apply repairs.

You can preconnect a folder at launch:

```bash
./scripts/run-workbench --project 'my-project=/absolute/path/with spaces/project'
```

Use `--port 8422` for a different local port, `--no-browser` to leave browser opening to you, and `--state-dir /absolute/private/folder` for isolated settings. Policies and private settings must stay outside inspected source. The offline exported preview is an inert recorded-demo inspector and cannot start new work.

## Command line and assistant connection

With a supported Python interpreter, inspect a saved UTF-8 error without running its command:

```bash
PYTHONPATH=src python3.12 -B -m shake_bake diagnose \
  --root /absolute/project/folder \
  --error-file /absolute/path/to/error.txt \
  --command 'npm test'
```

The JSON report preserves the error. Text export contains the same complete debugging brief, including unmatched locations and partial-result limits. Exit `0` means source was located, `3` means none was located, and `2` means the request was refused. None means the bug is fixed.

For a source question:

```bash
PYTHONPATH=src python3.12 -B -m shake_bake brief \
  --root examples/review-fixture \
  --task 'Find the executable slice coverage guard.'
```

Add `--style evidence` for every selected excerpt, or `--format json` for structured output. Optional local-model and policy-based commands are documented in [the helper contract](docs/helper-contract.md) and [routing guide](docs/routing-implementation.md).

The optional `mcp` extra supplies the official-SDK `shake-bake-mcp` stdio adapter. See [shared GUI/assistant setup](docs/shared-coordinator.md) and [actual host check boundaries](docs/codex-host-handoff.md). This standalone application does not depend on another project.

## Development and limits

[CONTRIBUTING.md](CONTRIBUTING.md) covers core tests, isolated wheel verification and browser checks. Committed workflow tests use disposable synthetic source. Passing them verifies mechanics and source integrity, not general diagnostic accuracy, security certification or model savings.

Source reads use descriptor-relative paths, reject symlinks and selected sensitive filenames, and retain exact bytes and hashes. This is not an operating-system or hostile-filesystem sandbox. Trusted root ancestors, hard links, bind mounts, kernel stalls, secret detection and cross-file atomic snapshots remain limitations. Windows needs an equivalent qualified read/process boundary before support.

Use [the documentation guide](docs/README.md) for technical details and dated experiments, [TODO.md](TODO.md) for priorities, [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for open release gates and [SECURITY.md](SECURITY.md) for reporting. The [original import](docs/import/2026-11-05.md) remains documented in Git history.

The application uses the [MIT license](LICENSE). Dependencies and model weights have separate terms; see [third-party notices](THIRD_PARTY_NOTICES.md), [model licenses](MODEL_LICENSES.json) and [the licensing plan](docs/LICENSING.md).
