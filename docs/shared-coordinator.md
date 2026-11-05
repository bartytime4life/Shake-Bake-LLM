# Shared local coordinator

Current update: `0.4.0.dev7` saves the shared Local AI choice across restart; see [preference boundaries](local-ai-preferences.md). The original `.dev4` implementation evidence below retains its stated scope. SDK 2.3.0 transport now has later development evidence; actual Claude/ChatGPT hosts remain unqualified.

Shared mode connects the GUI and prepared assistant adapter to one real owner-thread/controller and one routed HelperSession. Projects, single-job admission, captured results, task categories, model-policy gates and this session's pause state are shared. The native loopback client is tested; actual official-SDK and Claude/ChatGPT interoperability still need qualification.

## Start the service and connect the adapter

From the extracted folder on Linux:

```bash
PYTHONPATH=src python3 -B -m shake_bake gui \
  --connection-file "$HOME/.local/state/shake-and-bake/connection.json"
```

This starts the existing local workbench and publishes a new private connection file. The parent must be owner-owned mode 0700; a new leaf directory is created private. The file is owner-owned mode 0600 and must be outside every inspected source root. Existing files are refused rather than overwritten. Do not paste its token into chat, source, logs or host tool arguments. The server never returns it in GUI state or tool results.

With the optional official MCP v2 SDK installed, the candidate stdio adapter command is:

```bash
PYTHONPATH=src python3 -B -m shake_bake.mcp_server \
  --connection-file "$HOME/.local/state/shake-and-bake/connection.json"
```

The adapter uses the official SDK for MCP stdio. Its internal connection to the workbench is a small authenticated local RPC, not an MCP HTTP server, remote service or OAuth implementation. No host configuration is installed automatically and no actual host connection has been qualified here.

Only `starter-demo` is exposed to the adapter by default. Configure a real project and explicitly permit its ID at service launch:

```bash
PYTHONPATH=src python3 -B -m shake_bake gui \
  --project work=/absolute/approved/project \
  --adapter-project work \
  --connection-file "$HOME/.local/state/shake-and-bake/connection.json"
```

Repeat `--adapter-project` to permit several configured IDs. Unlisted projects and their jobs cannot be read or cancelled by this adapter token. Native requests cannot add roots, replace models, alter policies or toggle settings. The GUI remains the owner control for its shared-session pause switch. Arbitrary paths and shell commands are not accepted through tools.

## What is shared

- Adapter-started tasks appear in the GUI's recent history with Assistant origin; GUI-started permitted tasks are visible through the adapter too.
- `start_task` takes an approved project ID, exact task and Code/Troubleshoot/Documents/Search category. The same routed policy and model gates apply as in the GUI.
- The pipeline fingerprint now includes the GUI, shared client, helper session/runner and adapter modules as well as evidence/worker/routing code. Exact external SDK/runtime/hardware identity still needs its separate qualification record.
- `get_result` remains compact; `fetch_evidence` returns captured exact excerpts on demand. Notes remain unverified and final-answer readiness stays false.
- The one-active-job limit applies across both entry points. The GUI pause cancels the shared service's owned active runner and keeps new jobs evidence-only.
- Closing one adapter client does not terminate the shared service or erase retained jobs. Work stays bounded by its existing deadline, and the GUI can observe/cancel it.

Advanced separate diagnostics require explicit `--standalone` plus project/model or evidence-only arguments. That mode has its own session and is outside the GUI switch's scope; it is not the normal connected-product path. The legacy direct HelperSession SDK smoke remains a separate diagnostic.

## Credential and transport limits

The private file permits only schema 1, numeric loopback port, host `127.0.0.1` and a bounded URL-safe token. Public hosts, non-private/symlink/oversized configuration files and injected authorization headers are refused. The client ignores proxy/host environment variables, follows no redirects and uses a ten-second shared request deadline with bounded JSON.

The endpoint checks exact Host, bearer capability and method/project scope; browser Origin/Fetch headers are refused on this native endpoint. GUI cookie/Origin/CSRF rules remain separate. Connection/body/resource bounds are still enforced. This design assumes a trusted single-owner local environment; it does not isolate malicious same-user processes or establish multi-user security. Independent review and deployment/daemon isolation remain open.

Clean service shutdown removes only its exact unchanged connection file. Failed publication cleans its newly created partial file. An owner replacement is preserved. A hard kill can leave a stale private file: confirm the old service is stopped and handle that file explicitly before restarting. There is no automatic stale-file deletion or durable job recovery. The normal GUI now saves its Local AI choice, while jobs still do not survive service restart, and stopping a client/runner does not prove Ollama stopped GPU work.

## UX changes in this build

The existing interface now includes first-run guidance, Assistant/Workspace labels in recent activity, a pinned completed request/job identity and an expandable full original request. An earlier brief is explicitly labeled when a newer job is preparing, fails or is cancelled. Busy/controller-timeout messages give a next action. These changes reuse the current interface; actual desktop/phone/browser interaction remains unverified.

Full guided project registration, automatic calibration, persistent model profiles and other settings, a connected host-delivery UI and durable recovery remain future slices in UX-WORKFLOW.md. Manual copy/export still means the user must paste the brief and obtain the host's final judgment.

## Qualification

Nineteen new tests use actual private files, loopback HTTP, the controller and bounded children. They cover shared results/origins, scoped access, policy/pause/cancel behavior, cross-client single-job admission, refused browser/invalid credentials, private-file publication/cleanup/permissions, configuration bounds and explicit CLI modes. Model service tests use a simulation. The full program suite passes 121 tests; this is not real-model accuracy or actual host interoperability.

On a dependency-enabled machine, run `PYTHONPATH=src python3 -B integration/mcp_shared_smoke.py` to qualify the real SDK through the internal bridge. Missing SDK causes a failure rather than a skipped pass. Then qualify each supported host separately using permitted inert source before sensitive-project trials.

Official references checked November 4, 2026: [SDK v2 tour](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/whats-new.md), [SDK deployment/Host guidance](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/run/deploy.md), [SDK authorization boundary](https://py.sdk.modelcontextprotocol.io/run/authorization/). The internal bridge described here is the app's implementation choice; these references are not certification of it.
