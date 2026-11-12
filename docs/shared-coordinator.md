# Shared local coordinator

Reviewed November 11, 2026 against the documented dev37 source candidate. [Current status](current-status.md) distinguishes that source from recorded main, hosted delivery and the owner's installed application. Shared Local AI persistence was introduced in dev7; see [preference boundaries](local-ai-preferences.md). The original dev4 evidence below retains its historical scope. SDK 2.3.0 transport and an [actual Codex evidence-only synthetic handoff/cancellation](codex-host-handoff.md) have separate scoped evidence; broader host behavior and actual Claude/consumer ChatGPT remain unqualified.

Shared mode connects the GUI and prepared assistant adapter to one real owner-thread/controller and one routed HelperSession. Projects, single-job admission, captured results, task categories, model-policy gates and this session's pause state are shared. Native loopback and installed SDK clients are tested; actual-host qualification remains limited to the synthetic Codex check above.

## Start the service and connect the adapter

From the extracted folder on Linux with a supported Python 3.11+ interpreter:

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

The optional extra pins SDK 2.3.0. The adapter uses it for MCP stdio; installing/running that adapter does not add a browser listener, cloud call or automatic model download. Its internal connection to the workbench is a small authenticated local RPC, not an MCP HTTP server, remote service or OAuth implementation. No host configuration is installed automatically. The later opt-in Codex smoke used a temporary configuration with only the inert demo exposed; it did not qualify private-source handoffs.

Only `starter-demo` is exposed to the adapter by default. Configure a real project and explicitly permit its ID at service launch:

```bash
PYTHONPATH=src python3 -B -m shake_bake gui \
  --project work=/absolute/approved/project \
  --adapter-project work \
  --connection-file "$HOME/.local/state/shake-and-bake/connection.json"
```

Repeat `--adapter-project` to permit several configured IDs. Unlisted projects and their jobs cannot be read or cancelled by this adapter token. Native requests cannot add roots, replace models, alter policies or toggle settings. The GUI remains the owner control for its shared-session pause switch. Tool arguments offer approved project IDs and task text, without a root-selection or command-execution argument; embedded text does not grant that authority.

The workbench can also connect a folder explicitly for its current local session. That action does not expand the adapter's launch-time permitted-ID set. There are at most eight total approved project IDs, including the bundled demo. A model or inspected source cannot grant approval.

## What is shared

- Adapter-started tasks appear in the GUI's recent history; API result/history metadata records `entry_point=assistant` or `workspace`. The compact current history UI shows the request/date/status rather than an origin badge. GUI-started permitted tasks are visible through the adapter too.
- `start_task` takes an approved project ID, exact task and Code/Troubleshoot/Documents/Search category. The same routed policy and model gates apply as in the GUI.
- The pipeline fingerprint includes the selected Python implementation modules for GUI/shared transport, helper/runner, readiness/preferences and failed-run parsing/screening, as well as evidence/worker/routing code. It does not attest external SDK/runtime/hardware or browser asset bytes; those need their separate identities and checks.
- `get_result` remains compact; `fetch_evidence` returns captured exact excerpts on demand. Notes remain unverified and final-answer readiness stays false.
- The one-active-job limit applies across both entry points. The GUI pause cancels the shared service's owned active runner and keeps new jobs evidence-only.
- Closing one adapter client does not terminate the shared service or erase retained jobs. Work stays bounded by its existing deadline, and the GUI can observe/cancel it.

Recent GUI task metadata includes native lifecycle `state`, actual `outcome` or null and boolean `evidence_available` from the existing bounded result read. It does not fetch source to build history. `DONE` plus denied/error outcome is failed; successful preparation without source is incomplete. Older metadata without outcome/availability stays completed and manually reviewable, without a prepared claim. A newer failure does not prevent startup restoring an earlier retained prepared/incomplete capture. These are browser-history facts, not a new MCP history tool. See [helper contract](helper-contract.md) and [browser API reference](api-reference.md).

The failed-run workflow is a separate GUI source-location check, with no model call and no extra MCP tool. It refuses a conflicting active preparation; the common banner exposes the actual source job and existing Stop action. A busy race reconciles service state read-only without replaying either operation. Optional recorded command text is never executed.

Advanced separate diagnostics require explicit `--standalone` plus project/model or evidence-only arguments. That mode has its own session and is outside the GUI switch's scope; it is not the normal connected-product path. The legacy direct HelperSession SDK smoke remains a separate diagnostic.

## Credential and transport limits

The private file permits only schema 1, numeric loopback port, host `127.0.0.1` and a bounded URL-safe token. Public hosts, non-private/symlink/oversized configuration files and injected authorization headers are refused. The client ignores proxy/host environment variables, follows no redirects and uses a ten-second shared request deadline. Its JSON request envelope is capped at 128 KiB and shared response at 1 MiB plus 16 KiB of transport allowance.

The endpoint checks exact Host, bearer capability and method/project scope; browser Origin/Fetch headers are refused on this native endpoint. GUI cookie/Origin/CSRF rules remain separate. Connection/body/resource bounds are still enforced. This design assumes a trusted single-owner local environment; it does not isolate malicious same-user processes or establish multi-user security. Independent review and deployment/daemon isolation remain open.

Clean service shutdown removes only its exact unchanged connection file. Failed publication cleans its newly created partial file. An owner replacement is preserved. A hard kill can leave a stale private file: confirm the old service is stopped and handle that file explicitly before restarting. There is no automatic stale-file deletion or adapter reconnection/replay. A new service publication requires an explicitly restarted/reconnected adapter. The normal GUI saves its Local AI choice, while jobs and in-app folder approvals do not survive service restart; stopping a client/runner does not prove Ollama stopped GPU work.

## Browser capture and recovery boundaries

The current workbench separates failed-run source location from source-brief preparation, with optional details and explicit folder connection. A pinned source brief retains its captured request/job identity while newer draft text is edited. Shared starting/running/unknown preparation remains visible across workflows. Copy feedback follows exact handoff text, including a changed layout, and one unsettled clipboard write is shared across both workflows.

Failed-run reports remain in the open tab through pending, failed, malformed and obsolete repeat checks. Captured JSON saves the displayed report rather than newer unsent edits; text/manual/copy handoff is gated while pending or inputs differ. The accepted report and credential warning change only with a valid current replacement. Browser Retry can explicitly renew an expired local cookie without reloading or replaying work; it does not restore service jobs or folder approvals. See [dev36 workbench checks](workbench-usability-2026-11-11.md) and [dev37 recovery checks](captured-report-recovery-2026-11-11.md).

The original dev4 implementation had no browser acceptance; November 5 [readiness](pc-readiness-2026-11-05.md) and [copy-recovery](copy-and-screening-2026-11-05.md) checks retain their narrower installed scope. Current synthetic checks do not establish representative desktop/phone usability or assistive-technology qualification. Automatic calibration, persistent model profiles, connected host delivery and durable jobs/reports remain future work in [the workflow plan](UX-WORKFLOW.md). Manual copy/export still requires the user to paste the brief and obtain the host's final judgment.

## Qualification

The original dev4 record covered nineteen added tests using actual private files, loopback HTTP, the controller and bounded children: shared results/origins, scoped access, policy/pause/cancel, cross-client single-job admission, browser/credential refusal, file publication/cleanup/permissions, configuration bounds and explicit CLI modes. Model service tests used a simulation. That full suite passed 121 tests; the later 176-test checkpoint previously listed here is also historical. Use [current status](current-status.md) for current validation and delivery, and [evaluation status](evaluation-status.md) for the separate model/host evidence. Program tests do not establish real-model accuracy or full host interoperability.

On a dependency-enabled machine, run `PYTHONPATH=src python3 -B integration/mcp_shared_smoke.py` to qualify the real SDK through the internal bridge. Missing SDK causes a failure rather than a skipped pass. Then qualify each supported host separately using permitted inert source before sensitive-project trials.

Official references checked November 4, 2026: [SDK v2 tour](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/whats-new.md), [SDK deployment/Host guidance](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/run/deploy.md), [SDK authorization boundary](https://py.sdk.modelcontextprotocol.io/run/authorization/). The internal bridge described here is the app's implementation choice; these references are not certification of it.
