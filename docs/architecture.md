# Standalone architecture

Shake & Bake prepares a local Ollama junior developer handoff that the user pastes into ChatGPT or Claude as the main developer. It owns its configuration and policy and requires no other application's code, service or dataset. The primary journey is source preparation, review and manual copy/paste. Evidence-only collection and failed-run source checks support that journey. The main developer owns final reasoning and implementation decisions; the local worker has no action authority. See [product purpose, component responsibilities and acceptance](product-purpose.md) and [current source, delivery and validation status](current-status.md). Versioned experiment and validation records retain their original scope.

## Current components

| Component | Implemented role |
| --- | --- |
| `collector.py` and `search.py` | Bounded read-only lexical discovery, anchored whole-line excerpt selection, controlling context, line ranges, hashes, cutoffs and refusals. |
| `troubleshoot.py`, `error_formats.py`, `pytest_formats.py` | Parse supported Python, pytest, Node.js and TypeScript output, retain explicit error/frame associations and locate bounded current source. A location is not a diagnosis. |
| `failure_service.py` and `failure_runner.py` | Run the source-location check in a separate supervised Linux child, with exact input/result binding and no command execution or model call. |
| `briefing.py` and `worker.py` | Evidence-preserving handoffs and optional bounded loopback Ollama preparation. Notes stay unverified. |
| `routing.py` | Task-specific owner-record gates, reported model/pipeline identity checks, explanations and evidence-only fallback. Shipped profiles remain unqualified. |
| `helper.py` and `job_runner.py` | Approved project IDs, one supervised Linux child, captured evidence and owned-job cancellation. Inspected source is not executed. |
| `gui.py` and `web/` | Two-workflow loopback workbench, explicit session-only folder connection, drafts, captured-report review, copy/export and shared Local AI control. |
| `shared.py` | Private connection-file publication and bounded authenticated local RPC for the optional shared stdio adapter. |
| `doctor.py` | Startup checks and explicit metadata-only Ollama checks. |
| `benchmarks/model_trial.py` | Checkpointed development trials and separate receipt-bound review, labeled human or AI. No automatic qualification or cloud client. |
| `mcp_server.py` | Optional official-SDK stdio adapter exposing the five preparation-session tools. It does not expose the failed-run source locator as another tool. |

## Flow and ownership

The owner approves launch-time roots or explicitly connects an absolute folder through the local workbench. Models and inspected source cannot select roots, authorize commands or change policy. Source reads stay within the selected project's read boundary.

- **Failed run:** the user pastes or loads error output, selects a project and optionally records the command and working folder. The locator parses supported locations and captures exact source around them. It does not run the command, import the project, call a model, establish the cause or apply a fix. The handoff retains the original output, explicit error/frame/evidence identities and missing evidence.
- **Source brief:** the user describes the task and explicitly prepares evidence. Deterministic collection runs first. Optional Local AI can draft unverified notes and a prompt under the current routing/candidate gates. The user reviews, copies or exports the captured brief; an existing Claude or ChatGPT conversation still performs the demanding reasoning and final answer. An explicitly selected CLI embedding reranker is also optional; it is not enabled by normal GUI/shared routing.

Neither workflow sends a handoff to a cloud host automatically. Copying text or opening a fixed assistant link does not prove delivery, host reasoning, source completeness or a correct answer.

The installed package, source-root ancestors and any explicitly used local daemon are trusted components. Source, pasted output and worker text remain untrusted data. No automatic model downloads, inspected-project writes or execution of inspected code are implemented. Manual copy/export can contain private source. Credential screening warns without changing captured bytes; it is not comprehensive sensitive-data protection.

## Capture ownership and recovery

Source jobs belong to the running service: at most eight handles, with approximately five-minute access expiry. `/api/state` recent entries include the native `state`, actual `outcome` or null, and `evidence_available` from the existing result-descriptor read; history does not fetch source again. `DONE` alone is not a prepared brief. The UI distinguishes prepared, incomplete and failed results, restores a retained prepared/incomplete capture, and leaves older metadata without these facts labelled completed for manual review. A later failed task cannot relabel or replace an earlier exact capture.

The failed-run workflow retains one accepted report in the open tab until a valid current response replaces it. Pending, refused, malformed, wrong-input or obsolete rechecks leave that report and its credential warning available. Captured JSON always saves the displayed report, including while newer inputs differ or a recheck is pending. Copy/text/manual handoff is gated during pending checks or changed inputs. A failed same-input recheck can restore handoff of the earlier capture with an explicit not-refreshed notice. Save needed JSON before replacement, reload or closing the tab.

Input revisions, source-pin revisions and session generations prevent late responses from replacing newer work. Retry connection can explicitly renew an expired browser session without reloading or replaying tasks/settings/checks. Browser drafts and model choices are conveniences, not durable result storage: source-task draft saving can be disabled or cleared; failed-run input is not saved as that draft. Session-only folder approvals and jobs do not survive service restart. See [capture recovery](captured-report-recovery-2026-11-11.md) and [the failed-run guide](failed-run-workflow.md).

## Limits and qualification

Search defaults are 1,000 supported files, 20,000 entries, eight directory levels and a cooperative five-second walk budget. Scoring and context passes have their own count/byte bounds and can continue after that walk budget. Up to four primary windows and six controlling-context windows fit within the ten-record cap, 16 KiB total selected source and a 2 KiB context sub-budget. Individual files are capped at 256 KiB. Whole-line fitting can shorten surrounding context; an anchor line that cannot fit is omitted with cutoffs. These limits do not establish exhaustive or semantically complete review.

One source-task Linux child has a 45-second alarm, 10 CPU seconds, 512 MiB address space and a 1 MiB result bound. Model preparation requests 8,192 context tokens and 1,024 output tokens with a 6,000-byte chat-text cap and shared 30-second client deadline. These are requested settings, not attested model execution. Source/model identity changes and invalid worker responses preserve evidence and withhold the unsupported note. Cancelling a client/child does not prove daemon GPU work stopped.

A failed-run check accepts up to 64 KiB UTF-8 error output and 4 KiB each of recorded command and working-folder text. It bounds parsing to 20 frames, ten source excerpts and 16 KiB captured source. Its child has a four-second alarm, three CPU seconds and 512 MiB address space; the parent allows five seconds before terminating/reaping it. The report is capped at 1 MiB. Unsupported formats, excluded paths and incomplete locations remain visible.

The GUI uses loopback, cookie/Origin/CSRF checks, eight active connection slots, an initial three-second idle timeout and a cooperative twelve-second connection deadline. The controller wait is eight seconds and browser API deadline fifteen seconds. Ordinary JSON request envelopes are capped at 128 KiB; the escaped failed-run envelope is capped at 512 KiB in addition to its field limits. Transport timeout is not proof that an accepted operation stopped. These controls do not provide multi-user isolation or full flood resistance. See [connection limits](connection-limits.md), [helper contracts](helper-contract.md) and [Known Issues](../KNOWN_ISSUES.md).

## Evaluation and next milestones

Use `benchmarks/task-lab/` for exposed synthetic development tasks, with grading keys outside each fixture root. Freeze unseen cases for accuracy qualification. Compare a well-configured native host, deterministic evidence and local-model notes using identical allowed source/tasks, retaining failures and unknown usage. A real project may later be an optional test input; it never becomes a required component of this helper.

Held-out final-task accuracy, broader host connections, complete owner-PC qualification, representative usability/assistive-technology review, independent security qualification, per-PC automatic tuning and whole-task savings remain pending. Persistent profile/calibration UX, durable job/report recovery, vision and execution/patch workflows are future work. Implemented local recovery and viewport checks do not close those gates.

The normal GUI saves the Local AI choice in private single-writer state; new installations start paused. The core has no runtime dependencies. Installing the optional pinned SDK extra enables MCP stdio; it does not start a browser listener or add cloud calls. Actual-host smoke checks are separately opt-in. External dataset replay accepts private owner-declared splits with frozen identities and separate grading keys, without promoting profiles or running a paired host study. See [Local AI preferences](local-ai-preferences.md), [external evaluation](held-out-evaluation.md) and [shared coordination](shared-coordinator.md).
