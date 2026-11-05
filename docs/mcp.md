# Optional MCP stdio adapter

The core requires only the standard library. The optional adapter is written against official `mcp==2.3.0`. API shape was checked against the [official v2 SDK](https://py.sdk.modelcontextprotocol.io/) and its [testing guidance](https://py.sdk.modelcontextprotocol.io/get-started/testing/) on November 4, 2026, then tested with an actual subprocess client. A provider host is a separate qualification gate.

## Install and configure

Install the built wheel with its `mcp` extra, or install from this checkout:

```bash
.venv/bin/python -m pip install '.[mcp]'
```

[requirements/mcp.lock](../requirements/mcp.lock) records exact, hashed transitive dependencies for reproducible qualification. The extra pins the direct SDK version; use the lock when reproducing the recorded check. No credentials are needed for local stdio.

Create an owner-controlled configuration from [the example](../examples/config.toml), with a state directory outside all inspected roots. Before connecting a host, run an inert project and inspect its packet locally.

An example host entry, to adapt to the host's actual supported configuration:

```json
{
  "mcpServers": {
    "shake-bake": {
      "command": "/absolute/path/to/venv/bin/shake-bake-mcp",
      "args": ["--config", "/absolute/path/to/config.toml"]
    }
  }
}
```

This repository does not write host settings or claim this entry works in every Claude or ChatGPT product. It does not establish a tunnel, intercept prompts, alter existing conversation context or change a subscription allowance.

## Tool flow

1. `start_job(project_id, request, selections)` accepts 1–4 objects with `path`, `start_line`, `end_line`. All ranges are explicit and bounded. It returns a job ID.
2. `get_result(project_id, job_id)` returns literal job status, original request, evidence and gaps. Stop polling after a terminal status.
3. `fetch_evidence(project_id, job_id, evidence_id)` returns the exact captured record. Its `snapshot_only` flag is true.
4. `cancel_job(project_id, job_id)` cancels an active scoped job and prevents late publication.

No tool registers roots, changes permissions, runs commands, applies patches or calls a cloud provider. Explicit trial arguments may select a pinned installed local candidate; the host cannot create qualification authority. Tool refusals are structured `status: refused` responses with a safe code/message. Unexpected I/O failures omit underlying file contents and host paths.

Only one process may own a state store. `--config` owns an independent diagnostic coordinator. To use the GUI's actual coordinator, launch it first, then run `shake-bake-mcp --connect /absolute/private/state/connection.json`. This private Unix-socket connection shares admission, routing, exact evidence and the session local-AI pause. See [the workbench guide](workbench.md). The public tool surface stays at four methods.

`start_job` now supports optional `task_kind`, `ai_mode`, `model` and `digest`. Omitted selections use bounded lexical discovery. The default `ai_mode: off` makes no Ollama calls. `best` requires owner-reviewed profiles; `trial` is an explicitly pinned unqualified candidate. No tool can register roots, download a model, invent a qualification record or call a cloud provider. The GUI's browser listener exists only when the owner explicitly launches the GUI.

## Reproduce the SDK transport check

After building and installing the wheel in a clean virtual environment with the pinned extra:

```bash
/path/to/test-venv/bin/python integration/mcp_stdio_smoke.py \
  --python /path/to/test-venv/bin/python
```

The client starts a real stdio server from a temporary working directory without checkout `PYTHONPATH`, lists exactly four tools, starts an inert job, polls its result, compares exact CRLF evidence, retrieves the same scoped evidence, verifies a refused project and tests traversal refusal. This proves the tested SDK pair exchanges these calls. It does not prove native host UX, provider delivery, unseen task quality or a security audit.

`integration/mcp_shared_smoke.py` separately starts an installed GUI service and an official SDK stdio client using `--connect`. It verifies the same job/evidence through both entry points, GUI pause affecting a native request, no model/provider calls, continued service access after the client closes, and normal private-publication cleanup.
