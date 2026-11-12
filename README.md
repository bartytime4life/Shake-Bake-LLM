# Shake & Bake

Use a locally running Ollama model as your **junior developer**, then paste its compact handoff into **ChatGPT or Claude as your main developer**. Ollama prepares source-backed notes, relevant code locations, questions and suggested next checks. The main developer reviews that work, makes the final decisions and helps implement and verify the solution.

The purpose is to reduce paid-model context and repeated preparation. Token reduction and subscription cost savings still require whole-task measurement. The app preserves your original request, exact source and gaps; nothing is sent to either chat service automatically. See [the product purpose and developer roles](docs/product-purpose.md).

**Development source: `0.4.0.dev38`. Linux and Python 3.11+ are required.** [Current status](docs/current-status.md) distinguishes this local candidate, recorded validation and installation boundaries.

## Open the app

```bash
git clone https://github.com/bartytime4life/Shake-Bake-LLM.git
cd Shake-Bake-LLM
./scripts/run-workbench
```

The launcher chooses a supported installed Python and opens `http://127.0.0.1:8421`. Keep its terminal running; stop it with **Ctrl+C**. Opening the HTML file directly shows launch instructions rather than starting the service. No model, package installation or download happens automatically.

## Prepare locally, then paste into your main developer chat

1. Start in **Prepare source brief**. Select **Connect folder** beside **Project** and approve the folder to inspect read-only.
2. Describe the task in your own words. The handoff retains this request unchanged.
3. Use **Local AI — Ollama junior developer** and **Model details** to choose local preparation. A new installation starts off. **Best tested** requires a reviewed profile; none is currently qualified. To deliberately try your already installed model, launch with `./scripts/run-workbench --allow-candidate-trials`, enable Local AI, select **Try a candidate — unqualified**, refresh installed models, choose one and acknowledge the trial. Use a trusted local Ollama daemon with cloud features disabled. No model is downloaded or silently substituted.
4. Select **Prepare brief**. Review the junior developer draft, exact evidence and gaps. If no usable model draft was produced, the result explicitly says **evidence-only**; you can still use it as source preparation.
5. Select **Copy brief**, paste it into your existing **ChatGPT or Claude** chat, and send. The handoff tells that assistant to act as the main developer, verify the junior's advice, request missing source and decide the implementation and checks.

**Starting points (default)** keeps the handoff compact. **Full evidence, cited answer** includes every captured excerpt. **Review & export** provides manual copying and text/JSON saves. Neither model can authorize commands, change project scope or apply repairs through this app. Ollama's draft is unverified advice.

## Gather evidence for a failed run

1. Select **Connect folder** beside Project to open **Connect project folder**, enter the absolute folder path containing the failing code, and confirm the connection. This approves read-only inspection for the running session.
2. Paste the complete error output, or select **Load error file** for a saved UTF-8 `.txt` or `.log` up to 64 KiB. Expand **Run details (optional)** to record the command that failed; it is never executed.
   If the command ran in a subfolder, enter **Folder where the command ran**, for example `services/api`. Leave it blank to use the connected project root. This choice controls relative locations only and is never inferred from the command.
3. Select **Find failing source**. Inspect the source, reported line and column, unmatched frames and suggested next checks.
4. Select **Copy debugging brief** to take the captured error, project context and exact source into Claude or ChatGPT. If clipboard access fails, select and copy the provided text manually. Nothing is sent automatically.

| Input | What the app checks |
| --- | --- |
| Python traceback | Exact file/line and whether the displayed statement matches current source. |
| pytest failure report | Default/long and short decorated test locations, keeping each failure separate and ignoring captured test output. |
| Node.js stack trace | Local V8 stack locations, starting with the first readable project frame. |
| TypeScript compiler output | File, line, column and the corresponding compiler diagnostic. |

ANSI terminal colors are ignored only while recognizing locations; the original output remains unchanged. Browser URLs, runtime internals, outside-project files and missing files remain explicit. Source maps and container-to-local path mapping are not inferred. An unsupported log produces an incomplete result.

Changing the project, error or recorded command marks the previous report outdated. Its captured JSON stays saveable, while copy and text handoff wait for a new accepted check. A late response cannot silently replace the report for newer input. Pasted errors and commands are not stored as browser drafts or sent to a model.

The recorded working folder is captured with the result and exports. It must remain inside the connected project; symlinks and parent traversal are refused. Changing it also makes the previous result outdated. Separate local previews now keep their browser sessions from replacing one another.

Loading a file stays in the open tab until **Find failing source**. Original file text and line endings are preserved; editing the error uses the edited text instead. Invalid files leave the current error unchanged. **Connect project folder** is available from either workflow and keeps the other workflow's inputs unchanged.

The optional **Try a labelled example** uses invented errors and bundled inert source. It does not demonstrate a failure on your computer. See [the quickstart](docs/quickstart.md) and [supported formats and limits](docs/failed-run-workflow.md).

## Selection and model limits

When there is no traceback, choose **Prepare source brief**, select your connected project and ask a concrete question, such as “Where is the retry limit applied after a failed sign-in?” Inspect the collected source before copying the brief into your AI chat. An empty result cannot be copied as a successful source handoff.

Selection is bounded lexical retrieval and may miss important context. Your receiving assistant supplies the final reasoning and may need more source. If that assistant already has full repository tools, direct inspection can be more useful; no general time, token or accuracy improvement is established.

Within each matching file, selection keeps the strongest request-term anchor first, maximizes additional weighted matching-line coverage in a second window, and removes overlapping source lines. Optional embedding scoring uses scaled cosine normalization to handle very large and very small finite coordinates. See [the algorithms and synthetic validation](docs/algorithm-upgrades-2026-11-11.md).

If surrounding lines exceed the source-byte limit, a window can be shortened around its strongest match. Only whole source lines are kept, and the workbench and copied briefs disclose missing surrounding context. A matching line that cannot itself fit is still omitted. See [byte-budget fitting](docs/excerpt-budget-fitting-2026-11-11.md).

Ollama supplies the junior developer draft for source briefs. It is separate from failed-run evidence checks, which make no model call. Evidence-only preparation is available when Local AI is off, unavailable or unqualified. Existing installations retain their saved Local AI choice. Read [model setup and trial boundaries](docs/pc-readiness-and-trials.md), [routing](docs/routing-implementation.md) and [evaluation status](docs/evaluation-status.md) before enabling model trials. The dev38 role prompt has a new identity and has not been qualified on real models; earlier prompt results do not qualify it.

## Local data and scope

- Connected folders are session-only. A restart requires reconnecting folders unless supplied at launch. Use **Retry connection** to reconnect without reloading: entered failures and captured reports stay in the open tab. Missing project approvals make the old report outdated; reconnect the folder and check again. Closing or reloading the tab discards its failure text and reports; save an export you need.
- Failed error checks preserve the last accepted report. **Download captured JSON report** saves that displayed capture even while a new check runs or inputs are outdated; copy and text export wait for an idle check with matching inputs. Source-brief history distinguishes failed tasks from prepared/incomplete captures and restores the latest usable capture on page load. See [recovery behavior and checks](docs/captured-report-recovery-2026-11-11.md).
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

Use [the documentation guide](docs/README.md) for current instructions, [the complete catalog](docs/catalog.md) for plans and historical evidence, [the HTTP reference](docs/api-reference.md) for internal endpoints, [TODO.md](TODO.md) for priorities, [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for open release gates and [SECURITY.md](SECURITY.md) for reporting. The [original import](docs/import/2026-11-05.md) retains its own byte-preservation record.

The application uses the [MIT license](LICENSE). Dependencies and model weights have separate terms; see [third-party notices](THIRD_PARTY_NOTICES.md), [model licenses](MODEL_LICENSES.json) and [the licensing plan](docs/LICENSING.md).
