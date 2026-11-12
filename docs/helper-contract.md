# Helper contract: correctness before savings

Shake & Bake prepares exact evidence and optional local-model notes for an existing AI chat. The workbench also locates source for pasted failed runs without calling a model. The host still makes the demanding judgment and final answer. A valid JSON response, evidence reference or confidence claim does not establish semantic correctness. See [current source and delivery status](current-status.md) and [architecture](architecture.md).

## Implemented session interface

| Method | Input | Result |
| --- | --- | --- |
| `list_projects` | None | Approved project IDs and selected mode. |
| `start_task` | Approved ID, exact task text, optional code/troubleshoot/documents/search category | Task handle or explicit refusal; no automatic retry on busy. |
| `get_result` | Task handle | Status, unverified notes and drafted prompt fields (`goal`, `focus`, `asks`, `approach`), every evidence reference, search gaps. |
| `fetch_evidence` | Task handle, E1 onward, at most ten records | Captured exact source, line range and file/excerpt hashes. |
| `cancel_task` | Task handle | Owned runner stopped and reaped, or terminal status. |

In shared mode, roots and model policy belong to the workbench owner; an explicitly connected GUI folder is not automatically exposed to the adapter. Standalone diagnostics use explicit launch-time roots and a fixed model or evidence-only choice. Tool arguments do not provide command execution, arbitrary root selection, replacement models or changed policy; text embedded in a task does not grant that authority. One active task, no automatic retry queue, eight retained jobs and approximately five-minute access expiry bound the session. Request/output streams use unlinked temporary files outside the inspected project. This is session state, not durable project memory.

The Linux child runs only this package's collector and optional loopback worker. It never imports or executes inspected-project code. Child limits are a 45-second alarm, 10 CPU seconds, 512 MiB address space and 1 MiB per output file/result. The request envelope is capped at 128 KiB and the exact task at 16,384 characters with valid UTF-8. Parent polling also detects an overdue task. Resource limits are containment measures, not an OS filesystem or network sandbox. Cancelling the runner does not prove that a separately running Ollama daemon stopped GPU work.

The runner pins its working directory and import path to trusted package code and starts Python with safe-path/no-site flags. An inspected checkout used as the caller's working directory cannot shadow the child package. Temporary streams explicitly use a location outside all approved source roots; a configuration with no external scratch location is refused. Launcher/package installation and root ancestors must still be trusted.

`ANSWER` is a preparation outcome, never a verified final answer. An evidence-only or withheld-note result can be `ABSTAIN` and still contain useful exact evidence. `DONE` means the child returned a result; that result can also be `DENY` or `ERROR`. Completed session results explicitly say `result_kind=preparation_result`, `final_answer_ready=false` and `requires_host_reasoning=true`. Worker notes remain `unverified_worker_interpretation`. All source references survive a worker's incorrect or incomplete summary. Search exclusions and cutoffs survive even when no evidence is selected.

Fetched source is a recorded snapshot, not a live reread. A later edit needs a new task. Host code must fetch the relevant exact evidence before grounded claims. It must inspect contradictions and coverage gaps, and request more evidence when needed. Instructions embedded in source or worker notes remain untrusted data. These rules do not prove that any model will follow them perfectly.

## Browser capture ownership

The internal [browser HTTP API](api-reference.md) is separate from the five MCP tools and uses its own cookie/Origin/CSRF checks. It includes explicit folder connection and failed-run source location, neither of which is added to the MCP tool surface. The failed-run command is recorded data, never executed. See that reference for endpoint schemas and request/field limits, and [architecture](architecture.md) for child-process bounds.

`GET /api/state` recent entries include native `state`, `outcome` or null and boolean `evidence_available`, derived from the existing bounded result-descriptor read without fetching source.

History presents `DONE` plus denied/error outcome as failed, and a successful preparation with/without evidence as prepared/incomplete. Older entries without outcome/availability remain completed and manually reviewable. Startup can restore the latest retained prepared/incomplete capture; it does not replay a task. Input, pin and session revisions reject obsolete browser responses.

A failed-run report belongs to the open tab, not the eight-job source-task store. Rechecking keeps the last accepted capture until a valid response for the current inputs/session replaces it. Pending, failed, malformed and obsolete checks leave that exact report saveable as captured JSON. Copy/text/manual handoff waits during pending work or differing inputs; an unsuccessful same-input recheck can reuse the earlier capture with an explicit not-refreshed notice. Credentials remain associated with the displayed capture. Save needed JSON before a successful replacement, reload or tab closure. [Recovery checks](captured-report-recovery-2026-11-11.md) do not add durable storage or establish current disk identity after capture.

## Host connection and current evidence

`mcp_server.py` uses the optional pinned official Python SDK 2.3.0 v2 interface. The core has no runtime dependencies; installing the extra does not start a browser listener, download a model or add cloud calls. Scoped stdio/shared checks and an actual Codex evidence-only synthetic handoff have [versioned receipts and repeatable checks](codex-host-handoff.md). Claude Code and consumer ChatGPT remain unqualified. The SDK supplies MCP stdio; the private workbench RPC is an internal transport, not a replacement MCP HTTP implementation. Current validation and delivery state are recorded separately in [current status](current-status.md).

The shared-mode command connects to the workbench coordinator through its private connection file; see [shared-coordinator.md](shared-coordinator.md). Its approved project IDs, routed policy and pause state are shared with the GUI. Start the installed service with `shake-bake-ui --connection-file "/absolute/private/connection.json"`, then the candidate adapter with `shake-bake-mcp --connection-file "/absolute/private/connection.json"`. Only explicitly exposed project IDs are available; the default is the inert demo.

On a dependency-enabled machine run the installed `integration/mcp_subprocess_smoke.py` and `integration/mcp_shared_smoke.py` checks before actual-host trials. The opt-in `integration/codex_host_smoke.py` uses a real cloud-backed host and existing login; it is not part of offline tests or CI. Its `active-cancel` scenario adds scoped evidence of cancellation and a fresh successful task using an explicitly stopped synthetic preparation runner. Disconnect/deadline/restart, private source and local-model orchestration remain unqualified. Advanced separate diagnostics require an explicit `--standalone --project "ID=/absolute/path" --model INSTALLED_MODEL` or `--evidence-only`; they have a separate session. No model downloads or permanent host configuration changes happen automatically.

## Correctness qualification

The injected-wrong-note test verifies labeling, final-answer flags and preservation of contrary source. It does not show that the helper or host detects the bug. Blind real-model trials must measure missed critical issues, false findings, unsupported claims, correct abstentions and final task success before token savings count as a benefit.
