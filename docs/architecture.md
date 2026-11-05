# Standalone architecture

Shake and Bake is a general local preparation helper for Claude or ChatGPT. It owns its configuration, data and model profiles. It can inspect any explicitly approved source project; it requires no application-specific code, service or dataset. Bundled evaluations use self-contained synthetic fixtures.

## Current components

| Component | Implemented role |
| --- | --- |
| `collector.py` and `search.py` | Bounded read-only discovery, exact excerpts, line ranges, hashes, cutoffs and refusals. |
| `briefing.py` and `worker.py` | Evidence-preserving handoffs and optional bounded loopback Ollama preparation. Notes stay unverified. |
| `routing.py` | Task-specific owner-record gates, reported model/pipeline identity checks, explanations and evidence-only fallback. Shipped profiles remain unqualified. |
| `helper.py` and `job_runner.py` | Approved project IDs, one supervised Linux child, captured evidence and owned-job cancellation. Inspected source is not executed. |
| `gui.py` and `web/` | Local task/evidence/model interface, copy/export and off switch. Connection admission and deadlines are bounded. |
| `doctor.py` | Startup checks and explicit metadata-only Ollama checks. |
| `benchmarks/model_trial.py` | Checkpointed development trials and separate receipt-bound human review. No automatic qualification or cloud client. |
| `mcp_server.py` | Prepared optional SDK adapter; SDK 2.3.0 transport has development evidence; actual host interoperability remains unqualified. |

## Flow and ownership

The user selects the job and an approved project. Ordinary code collects bounded exact evidence. An eligible local model can organize it into a short note with references and questions. Claude or ChatGPT still makes the demanding judgment and final answer. Source cutoffs, contradictions and unsupported conclusions must remain visible.

The app's installed package, source-root ancestors and local daemon are trusted components. Source and worker text are untrusted data. No automatic model downloads, inspected-project writes, execution of inspected code or cloud-provider calls are implemented. Manual copy/export is explicit and can contain private source; permitted handling still needs qualification.

## Limits and qualification

Search defaults are 200 supported files, 4,000 entries, eight directory levels, a cooperative five-second scan budget, four windows and 16 KiB of selected excerpts. Individual files are capped at 256 KiB. These limits do not establish exhaustive review.

One Linux task child has 45 seconds wall time, 10 CPU seconds, 512 MiB address space and bounded output. Model preparation requests up to 8,192 context tokens and 512 output tokens with a 6,000-byte message cap and shared 30-second client deadline. Source/model identity changes and invalid responses preserve evidence and refuse an unsupported prepared answer. Cancelling a client/child does not prove daemon GPU work stopped.

The GUI uses loopback, request/session checks, eight active connection slots, an initial three-second idle timeout and a cooperative twelve-second connection deadline. These controls do not provide multi-user isolation or full flood resistance. See connection-limits.md and the root KNOWN_ISSUES.md for tested scope and open gates.

## Evaluation and next milestones

Use `benchmarks/task-lab/` for exposed synthetic development tasks, with grading keys outside each fixture root. Freeze unseen cases for accuracy qualification. Compare a well-configured native host, deterministic evidence and local-model notes using identical allowed source/tasks, retaining failures and unknown usage. A real project may later be an optional test input; it never becomes a required component of this helper.

Held-out final-task accuracy, actual host connections, complete owner-PC qualification, broader desktop/phone accessibility review, independent security qualification, per-PC automatic tuning and cloud savings remain pending. Persistent profile/calibration UX, durable GUI recovery, embeddings, vision and execution/patch workflows are future work.

The normal GUI saves the Local AI choice in private single-writer state; new installations start paused. Jobs remain session-only. External dataset replay now accepts private owner-declared splits with frozen identities and separate grading keys, without promoting profiles or running a paired host study. See local-ai-preferences.md and held-out-evaluation.md.
