# Helper contract: correctness before savings

Shake and Bake prepares evidence and local model notes for Claude or ChatGPT. The host still makes the demanding judgment and final answer. A valid JSON response, evidence reference or confidence claim does not establish semantic correctness.

## Implemented session interface

| Method | Input | Result |
| --- | --- | --- |
| `list_projects` | None | Approved project IDs and selected mode. |
| `start_task` | Approved ID, exact task text | Task handle or explicit refusal. |
| `get_result` | Task handle | Status, unverified notes, every evidence reference, search gaps. |
| `fetch_evidence` | Task handle, E1–E4 | Captured exact source, line range and hashes. |
| `cancel_task` | Task handle | Owned runner stopped and reaped, or terminal status. |

Roots and model names are owner launch configuration. Tool callers cannot supply shell commands, arbitrary source paths or replacement models. One active task, no automatic retry queue, eight retained jobs and five-minute access expiry bound the session. Request/output streams use unlinked temporary files outside the inspected project. This is session state, not durable project memory.

The Linux child runs only this package's collector and optional loopback worker. It never imports or executes inspected-project code. Child limits are 45 seconds wall time, 10 CPU seconds, 512 MiB address space and 256 KiB per output file. Parent polling also detects an overdue task. Resource limits are containment measures, not an OS filesystem or network sandbox. Cancelling the runner does not prove that a separately running Ollama daemon stopped GPU work.

The development-2 runner pins its working directory and import path to trusted package code and starts Python with safe-path/no-site flags. An inspected checkout used as the caller's working directory cannot shadow the child package. Temporary streams explicitly use a location outside all approved source roots; a configuration with no external scratch location is refused. Launcher/package installation and root ancestors must still be trusted.

`ANSWER` in the legacy evidence schema means evidence was collected. Session results explicitly say `result_kind=preparation_result`, `final_answer_ready=false` and `requires_host_reasoning=true`. Worker notes remain `unverified_worker_interpretation`. All source references survive a worker's incorrect or incomplete summary. Search exclusions and cutoffs survive even when no evidence is selected.

Fetched source is a recorded snapshot, not a live reread. A later edit needs a new task. Host code must fetch the relevant exact evidence before grounded claims. It must inspect contradictions and coverage gaps, and request more evidence when needed. Instructions embedded in source or worker notes remain untrusted data. These rules do not prove that any model will follow them perfectly.

## Host connection and current evidence

`mcp_server.py` uses the optional official Python SDK's v2 interface. Installed SDK 2.3.0 stdio/shared checks have passed, and one actual Codex evidence-only synthetic handoff now has [a scoped receipt and repeatable check](codex-host-handoff.md). Claude Code and consumer ChatGPT remain unqualified. The SDK supplies MCP stdio; the private workbench RPC is an internal transport, not a replacement MCP HTTP implementation.

The shared-mode command connects to the workbench coordinator through its private connection file; see [shared-coordinator.md](shared-coordinator.md). Its approved project IDs, routed policy and pause state are shared with the GUI. Start the service with `gui --connection-file /absolute/private/connection.json`, then the candidate adapter with `shake-bake-mcp --connection-file /absolute/private/connection.json`. Only explicitly exposed project IDs are available; the default is the inert demo.

On a dependency-enabled machine run the installed `integration/mcp_subprocess_smoke.py` and `integration/mcp_shared_smoke.py` checks before actual-host trials. The opt-in `integration/codex_host_smoke.py` uses a real cloud-backed host and existing login; it is not part of offline tests or CI. Its synthetic scope does not qualify active cancellation, failure/recovery, private source or local-model orchestration. Advanced separate diagnostics require an explicit `--standalone --project ID=/absolute/path --model INSTALLED_MODEL` or `--evidence-only`; they have a separate session. No model downloads or permanent host configuration changes happen automatically.

## Correctness qualification

The injected-wrong-note test verifies labeling, final-answer flags and preservation of contrary source. It does not show that the helper or host detects the bug. Blind real-model trials must measure missed critical issues, false findings, unsupported claims, correct abstentions and final task success before token savings count as a benefit.
