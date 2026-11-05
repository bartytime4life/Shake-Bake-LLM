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

No tool registers roots, changes permissions, runs commands, selects models, applies patches or calls a cloud provider. Tool refusals are structured `status: refused` responses with a safe code/message. Unexpected I/O failures omit underlying file contents and host paths.

Only one process may own a state store. Close the MCP server before using separate CLI commands on that store, or give independent diagnostic sessions separate stores. A shared GUI/host coordinator remains a future slice.

## Reproduce the SDK transport check

After building and installing the wheel in a clean virtual environment with the pinned extra:

```bash
/path/to/test-venv/bin/python integration/mcp_stdio_smoke.py \
  --python /path/to/test-venv/bin/python
```

The client starts a real stdio server from a temporary working directory without checkout `PYTHONPATH`, lists exactly four tools, starts an inert job, polls its result, compares exact CRLF evidence, retrieves the same scoped evidence, verifies a refused project and tests traversal refusal. This proves the tested SDK pair exchanges these calls. It does not prove native host UX, provider delivery, unseen task quality or a security audit.
