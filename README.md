# Shake & Bake LLM

Prepare exact local evidence for Claude, ChatGPT, or a human reviewer. Keep routine collection on your computer and hand off the original request, source excerpts, hashes and visible gaps when reasoning is needed.

This is a standalone application. It has its own configuration and private data store and does not depend on another business application.

**Current checkout: `0.1.0.dev0`, a working repository bootstrap.** The [Google Drive plan](https://docs.google.com/document/d/1llXN3-oNzIWi7DL1yU3KwXK_tE-RaBqrXRjPwE5Y-3s/edit) records a separate `0.4.0.dev4` prototype. That archive has not been imported; its reported 121 tests are not results for this checkout. See the [planning source record](docs/planning/source-record.md) and [roadmap](TODO.md).

## Try the offline demo

Linux and Python 3.11+ are the initial supported environment. The core has no third-party runtime dependencies.

```bash
PYTHONPATH=src python3 -m shake_bake doctor
PYTHONPATH=src python3 -m shake_bake demo
```

The demo creates synthetic source and a private temporary store, collects three lines, emits JSON, and removes its temporary files. It contacts no service and executes no inspected repository code.

To install in your own virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/shake-bake demo
```

## Prepare a real evidence packet

Copy [the example configuration](examples/config.toml) somewhere outside inspected repositories and replace the project root with an absolute path you approve. The private state directory must be outside every inspected root. Existing state directories require mode `0700`; files require `0600` and your ownership. Keep configuration under your control.

```toml
schema_version = 1
state_dir = "~/.local/state/shake-bake"

[projects.my_project]
root = "/absolute/path/to/your/project"
```

Then select exact one-based inclusive ranges:

```bash
shake-bake prepare --config /path/to/config.toml --project my_project \
  --request 'Prepare evidence for investigating this startup failure.' \
  --select src/app.py:10:35 --select tests/test_app.py:1:40
```

Use `--request-file /path/to/request.txt` to preserve a longer UTF-8 request, including its whitespace and newlines. JSON goes to stdout. Redirecting it to a file is an explicit local export; that file can contain private source. Review it before giving it to an assistant. Avoid putting private requests directly into shell history.

The receipt contains a `job_id`. Retrieve it later from the idle store:

```bash
shake-bake result --config /path/to/config.toml --project my_project --job JOB_ID
shake-bake evidence --config /path/to/config.toml --project my_project --job JOB_ID --id EVIDENCE_ID
```

`prepared` means all requested excerpts were captured. `incomplete` preserves available evidence and exact refusal codes. Neither status means the original investigation was solved. Ctrl+C cancels an active CLI job. Failed or cancelled jobs publish no completed packet. Exit codes: `0` success, `2` incomplete/refused/failed, `130` interruption.

## Optional MCP adapter

The optional adapter uses the official Python MCP SDK, pinned to `2.3.0`. Install the extra only if you need it:

```bash
.venv/bin/python -m pip install '.[mcp]'
.venv/bin/shake-bake-mcp --config /absolute/path/to/config.toml
```

This is a **local stdio** server with four tools: `start_job`, `get_result`, `fetch_evidence`, `cancel_job`. Project IDs come from the owner-controlled config; tool callers cannot register arbitrary roots. The app writes its own local receipts and reads approved source. It runs no model, shell command or provider request. The adapter does not open an HTTP port or install itself into a host.

See [adapter setup and qualification](docs/mcp.md) for an example host entry, pinned dependency installation and the real subprocess test. Each actual Claude/ChatGPT host still needs separate qualification. Evidence returned to a connected host may be sent to that host's provider.

## Boundaries and limits

- Up to four ranges per job; up to 200 lines and 32 KiB per range; bounded UTF-8 source files up to 256 KiB; original request up to 16 KiB.
- POSIX descriptor-relative reads reject traversal, hidden paths, symlink components, hard links, special files, credential filenames and detected secret patterns.
- File hashes cover the whole captured file. Excerpts retain LF/CRLF bytes. Captures detect ordinary in-place and path-replacement races; they are snapshots, not a live repository view.
- One active job and one cooperating coordinator per private store. Cancellation wins over late completion. An interrupted receipt becomes failed on restart; jobs are not automatically resumed.
- Cooperative 30-second collection deadline and 1,000-receipt capacity. This is not an OS filesystem, network or resource sandbox. See [security boundaries](docs/security-boundaries.md).

The bootstrap has no GUI, Ollama worker, automatic retrieval/routing, code execution, patch application, cloud API calls or measured token savings. Those remain explicit work items. Windows collection is unqualified.

## Develop and verify

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src
```

[CONTRIBUTING.md](CONTRIBUTING.md) covers wheel builds, optional MCP tests and evidence standards. CI runs the core suite on Python 3.11–3.14 and separately exercises a wheel-installed MCP client/server pair. The project is MIT licensed; [third-party notices](THIRD_PARTY_NOTICES.md) distinguish application code, optional dependencies and inspected source.
