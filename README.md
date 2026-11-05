# Shake & Bake LLM

A standalone local workbench that prepares exact source evidence for your assistant. Ordinary code collects the source; optional Ollama notes stay visibly separate; Claude, ChatGPT or a human makes the final judgment.

**Current version: `0.2.0.dev0`.** This repository now has a working GUI, bounded lexical discovery, conservative Ollama routing, private job storage and a shared native MCP coordinator. It does not depend on another business application. The Drive plan's separate `0.4.0.dev4` archive has not been imported; no parity with it is claimed.

## Open the workbench

Linux and Python 3.11+ are the initial environment. The core and GUI use the Python standard library, with no mandatory third-party runtime package or frontend service.

```bash
PYTHONPATH=src python3 -m shake_bake gui
```

This opens a private loopback session with bundled synthetic source. To deliberately allow local installed-model trials on that inert demo:

```bash
PYTHONPATH=src python3 -m shake_bake gui --enable-local-ai
```

No model is downloaded or daemon started. In Model details, refresh installed models, choose **Try a candidate — unqualified**, select a pinned model and acknowledge the trial. **Best tested** uses reviewed profiles only; no qualifying record keeps preparation evidence-only. See [Ollama routing](docs/ollama-routing.md).

The interface provides project/task selection, exact evidence, visible gaps, model settings, recent briefs, stop controls, pinned request/job identity, and copy/JSON export. The selected model and preferences survive restart, including when Ollama is offline. See [the workbench guide](docs/workbench.md) for launch/session behavior and limitations.

## Approve your own project

Copy [the example](examples/config.toml) outside inspected repositories, then edit its root and private state path:

```toml
schema_version = 1
state_dir = "~/.local/state/shake-bake"

[projects.my_project]
root = "/absolute/path/to/your/project"

[ollama]
enabled = false
port = 11434
```

```bash
shake-bake gui --config /path/to/config.toml
```

The state store and any profile policy must be outside all inspected roots. The UI cannot expand root grants. For private source, use a trusted local Ollama daemon with cloud features disabled; client metadata checks cannot attest its upstream behavior.

## CLI and installation

```bash
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/shake-bake doctor
.venv/bin/shake-bake demo
```

Prepare a source brief with bounded lexical discovery:

```bash
shake-bake prepare --config /path/to/config.toml --project my_project \
  --request 'Investigate the startup failure.' --task-kind troubleshoot
```

Add `--select src/app.py:10:35` for explicit one-based inclusive ranges, or `--request-file /path/to/task.txt` to retain request whitespace/newlines. JSON goes to stdout. Use `--local-ai off` (default), `best`, or an explicit pinned `trial`; [routing setup](docs/ollama-routing.md) gives the commands. `result` and `evidence` retrieve captured receipts from an idle store.

## Optional native MCP

Install the pinned official SDK extra: `.venv/bin/python -m pip install '.[mcp]'`. To share the GUI's actual job, routing and pause state:

```bash
shake-bake-mcp --connect /absolute/private/state/connection.json
```

The four tools are `start_job`, `get_result`, `fetch_evidence` and `cancel_job`. A separate `--config` diagnostic mode remains available. No host settings, public endpoint, tunnel or provider account is installed/configured. [MCP setup](docs/mcp.md) and [shared coordinator details](docs/workbench.md) distinguish SDK transport checks from actual native-host qualification.

## Evidence and safety boundaries

The original request and captured UTF-8/LF/CRLF source stay exact, with file/excerpt hashes and line ranges. Source is untrusted data; it cannot authorize tools or change policy. `prepared` means evidence capture, never a solved investigation. Invalid/failed model notes are discarded while exact evidence remains available. Missing usage/savings remains unknown.

Collection allows four ranges, up to 200 lines/32 KiB per range and 256 KiB per file. Lexical discovery adds bounded scans and visible exclusions/cutoffs. Traversal, symlinks, hard links, special files, credential paths and detected secret patterns are refused. Secret screening is heuristic. A private SQLite store persists scoped job receipts; cancellation wins over late output and interrupted jobs fail on restart.

There are no inspected-source commands, patch application, automatic model downloads, cloud API calls or measured savings. This is not an OS sandbox or an independently qualified release. Real model accuracy, full hardware calibration, native-host UX and Windows still need separate evidence. Read [security boundaries](docs/security-boundaries.md) and [the work queue](TODO.md).

## Verify and contribute

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src
node --check src/shake_bake/web/app.js
```

Node is only a development syntax check, not an application runtime. [CONTRIBUTING.md](CONTRIBUTING.md) covers clean-wheel and real SDK subprocess checks. The original [Drive plan](https://docs.google.com/document/d/1llXN3-oNzIWi7DL1yU3KwXK_tE-RaBqrXRjPwE5Y-3s/edit), [source record](docs/planning/source-record.md), implementation docs and dated validation records separate current results from historical prototype claims. MIT licensed; [third-party notices](THIRD_PARTY_NOTICES.md) cover the optional SDK and bundled icons.
