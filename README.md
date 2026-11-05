# Shake and Bake LLM Assistant

A standalone local preparation helper for Claude or ChatGPT, with an Ollama worker option. Ask a repository question and get a traceable source handoff. Claude or ChatGPT supplies the demanding judgment and final answer. The diagnostic evidence path needs no model, network connection or runtime package beyond Python 3.11+.

**Current source: `0.4.0.dev4`, imported from the tested standalone development package.** This replaces the separate `0.1.0.dev0` repository bootstrap while preserving it in Git history. The original runtime, tests, fixtures and technical documentation have been recovered; see the [import and publication review](docs/import/2026-11-05.md). This is a development preview, not a qualified production release.

| Status | Scope |
| --- | --- |
| Implemented | Exact evidence collection, bounded lexical retrieval, optional loopback Ollama preparation, local workbench, owner-record model gates, shared GUI/adapter job coordination, scoped project access and cancellation. |
| Verified in development | 121 program tests; synthetic retrieval and ten exposed evidence-only Task Lab cases. Model-service tests use simulations. Current import validation is recorded separately from historical receipts. |
| Prepared, unqualified | Optional official-SDK MCP adapter and integration scripts; actual Claude/ChatGPT handoffs still need separate checks. |
| Planned | Guided setup, automatic per-PC calibration, persistent profiles/preferences, durable job recovery and direct cloud-provider clients. |
| Unverified or unmeasured | Owner-PC behavior, real-model accuracy/performance, actual host delivery, desktop/phone/browser interactions, Windows support, independent security qualification and whole-task cloud savings. |

## Get the source

```bash
git clone https://github.com/bartytime4life/Shake-Bake-LLM.git
cd Shake-Bake-LLM
PYTHONPATH=src python3 -B -m shake_bake doctor
```

Use Linux and Python 3.11+ for development. Run the model-free demo below before approving any real source. For reproducible core tests, wheel installation and optional SDK checks, follow [CONTRIBUTING.md](CONTRIBUTING.md). No model weights or third-party runtime distributions are bundled.

The [prioritized to-do list](TODO.md) puts real-machine/model accuracy, host delegation and measured benefit first. Every pending item has a completion check; the [PC checklist](docs/PC-CHECKLIST.md) supplies the detailed runbook.

The [whole-workflow UX plan](docs/UX-WORKFLOW.md) connects first setup, shared job/policy state, local preparation, evidence review, handoff and recovery. It records current code-level gaps and planned implementation slices; browser/user-flow qualification remains pending.

Shake and Bake is a standalone app with its own configuration, test fixtures and data. Its bundled code evaluations use self-contained synthetic projects; no other application is required.

The original app uses the existing [MIT license](LICENSE), which permits commercial reuse and resale with its required notice retained. External dependencies and model weights have separate terms. Read [the licensing plan](docs/LICENSING.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [model-license registry](MODEL_LICENSES.json). Exact model-artifact redistribution review remains pending. Building a wheel requires setuptools 77+; running the source app adds no runtime dependency.

Before release or feature promotion, review [Known Issues and release expectations](KNOWN_ISSUES.md) and the security/bug gates in the [PC checklist](docs/PC-CHECKLIST.md). Unverified security, accuracy and integration checks remain pending; the program-test count is not a security certification.

The local web server now caps active connections, expires stalled requests and cancels expired queued operations. See [connection limits and regression evidence](docs/connection-limits.md); broader load/security qualification remains pending.

## Shared GUI and assistant work

The [shared-coordinator guide](docs/shared-coordinator.md) connects the workbench and prepared adapter to the same routed jobs, captured evidence and session pause state. Private connection files and explicit project scopes are tested. The interface adds first-run help, job-origin labels and pinned completed-result identity. Actual SDK/host and browser interaction qualification remains pending.

## Open the visual workbench

On Linux, from the extracted `shake-and-bake` folder:

```bash
PYTHONPATH=src python3 -B -m shake_bake doctor
PYTHONPATH=src python3 -B -m shake_bake gui
```

This opens the loopback-only browser interface at `http://127.0.0.1:8421`. It includes a bundled inert demo, task cards, an evidence map, expandable model statistics/selection details, exact source receipts, copy/download controls and a local-AI off switch. No model installation is needed for the evidence-only demo. Published benchmarks and owner-recorded local trials have separate labels.

Add an approved source folder at launch with `--project my-project=/absolute/project/folder`; choose it from the interface. Use `--policy /absolute/path/outside-the-project/routing.json` for an owner policy. `--no-browser` starts the service without opening a browser; `--port 8422` selects a different local port. Installed packages also provide `shake-bake-ui`.

The offline preview is a **recorded demo inspector**, with synthetic source and no model inference. It is a separate export; it does not run new jobs. Read [the workbench guide](docs/visual-workbench.md) for scope and setup. Cloud-browser visual QA was blocked by automatic approval review, so desktop/phone rendering and live browser interactions remain unverified. The backend and JavaScript syntax checks passed.

## Prepare a real model trial

Start with the [Run on your PC checklist](docs/PC-CHECKLIST.md). Every owner-PC item stays unchecked until actually verified there.

The [per-PC calibration plan](docs/per-pc-calibration.md) and [Your computer & tuning GUI design](docs/per-pc-calibration-ui.md) explain the next hardware-aware milestone. Automatic tuning and that new dashboard remain planned.

The startup check and repeatable trial runner are ready. They record reported model identity, settings, source integrity, per-attempt failures and a separate grading sheet. Accuracy stays unset until review. Start with the [PC readiness and trial guide](docs/pc-readiness-and-trials.md). The [open-gap review](docs/open-gaps.md) records what still needs proving, including native-host comparison and actual hardware behavior. No trial automatically promotes a model.

## Run the working demo

From the extracted `shake-and-bake` directory on Linux:

```bash
PYTHONPATH=src python3 -B -m shake_bake brief \
  --root examples/review-fixture \
  --task "Find executable slice coverage and provide exact evidence."
```

Use `--format json` for structured output. For your own source, select a trusted, quiescent project root. The program prints to stdout and does not execute selected source or save output in that project. `-B` disables Python bytecode-cache writes.

Each brief retains the original request, relative paths, line ranges, unchanged excerpts, hashes, exclusions and cutoff reasons. It is an evidence handoff, not a completed review or safety verdict. Lexical selection is not exhaustive coverage.

## Optional local Ollama worker

Add `--model` with the exact name of an already installed local model. The client targets `127.0.0.1:11434`; `--ollama-port` changes only the port. No server starts and no model downloads automatically.

```bash
PYTHONPATH=src python3 -B -m shake_bake brief \
  --root examples/review-fixture \
  --task "Find executable slice coverage and provide exact evidence." \
  --model qwen3:8b
```

That model is an example, not a detected installation. The client checks `/api/show` before sending source and refuses known cloud names and reported remote models. It ignores proxy/host environment variables and follows no redirects. A shared 30-second deadline, bounded responses, conservative message-byte cap, 512 generated tokens and an 8,192-token requested context bound preparation.

Configure the trusted Ollama daemon with cloud features disabled first: [official guidance](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features). Ollama documents `OLLAMA_NO_CLOUD=1` or its daemon configuration setting, followed by a restart. Setting a variable on this client does not reconfigure an existing server. The client cannot attest model weights, enforce the daemon's network policy, prove every custom template fits, or guarantee GPU-work cancellation after disconnect.

Notes stay labeled unverified. Unknown references, added fields, tool calls, duplicate JSON keys, truncated replies and model mismatches are refused. Every selected source remains visible. Worker failure retains evidence and returns `ABSTAIN`.

## Task interface and prepared connection

The new Linux `HelperSession` accepts tasks only for owner-configured projects. It runs one bounded preparation child, returns compact notes and every source reference, serves captured exact evidence on demand, and cancels its own runner. Configure an explicit local model for normal helper mode, or explicitly choose evidence-only diagnostics.

Every completed preparation result sets `final_answer_ready=false` and `requires_host_reasoning=true`. Worker confidence is never a verification signal. Tests check that an injected incorrect note stays unverified and cannot remove source. They do not prove that a model detects the incorrect note.

The optional `mcp` extra and `shake-bake-mcp` entry point prepare an official-SDK stdio adapter. **SDK interoperability and actual Claude/ChatGPT connections are unverified.** The SDK is absent in this development environment. See [helper-contract.md](docs/helper-contract.md) for the five methods, candidate launch command and qualification gate. `integration/mcp_shared_smoke.py` prepares the shared-path SDK check; the legacy `mcp_smoke.py` is a separate diagnostic. Neither is counted in the passed base suite.

## Accuracy-gated model choice

The `assist` command adds a task-specific policy selector, a “why this model” explanation and a local-AI off switch:

```bash
PYTHONPATH=src python3 -B -m shake_bake assist \
  --root examples/review-fixture \
  --task-kind code \
  --task "Find executable slice coverage." \
  --policy examples/routing-policy.json
```

All shipped profiles are unqualified candidates. This example returns exact evidence and explains why no model was selected; exit 3 indicates that no model-prepared handoff was produced. It makes no inventory or model call. Add `--disable-local-ai` to explicitly bypass local AI; the policy is then optional. `--format json` returns the decision and preparation result.

Owner policies live outside inspected source roots. Comparable, reviewed held-out records must meet the paired native baseline with no recorded critical misses or unsupported critical claims. Model digest and pipeline identity must match; latency only breaks accuracy ties. The routed worker checks reported local inventory before source submission and after inference. These checks rely on trusted owner review records and daemon metadata; they are not an accuracy certificate or weight-byte attestation. See [routing-implementation.md](docs/routing-implementation.md).

## Verification

```bash
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
PYTHONPATH=src python3 -B benchmarks/evaluate_selection.py
```

The current candidate passed 121 program tests. HTTP model tests use a simulated loopback service, not a real model; GUI tests exercise the actual loopback HTTP server and real bounded preparation children. Routing tests use explicitly fabricated qualification records. The task lab supplies ten exposed jobs with independent grading keys outside each fixture root. All ten retain their required source spans on the diagnostic path. This is mechanical evidence coverage, not model accuracy. The saved previous candidate retained the required spans in nine of ten cases; the distant-condition case motivated the two-window retrieval change.

```bash
PYTHONPATH=src python3 -B benchmarks/run_task_lab.py --evidence-only
```

See [the Task Lab guide](benchmarks/task-lab/README.md) before a real model replay. Its grading fields remain pending until separately reviewed. The bundled synthetic retrieval variants and ten-case Task Lab supply the development evidence; no blind defect detection or token-savings result is claimed.

## File map

| Path | Role |
| --- | --- |
| `src/shake_bake/contracts.py` | Immutable evidence records and refusals. |
| `src/shake_bake/collector.py` | Descriptor-relative source reads and hashes. |
| `src/shake_bake/search.py` | Bounded lexical discovery and selection. |
| `src/shake_bake/worker.py` | Optional loopback Ollama client and validation. |
| `src/shake_bake/briefing.py` | Evidence-preserving handoffs. |
| `src/shake_bake/cli.py` | Explicit-file CLI and new brief workflow. |
| `src/shake_bake/helper.py` | Bounded task sessions and captured-evidence access. |
| `src/shake_bake/job_runner.py` | Supervised Linux preparation child. |
| `src/shake_bake/shared.py` | Private connection-file lifecycle and bounded shared-service client. |
| `src/shake_bake/mcp_server.py` | Prepared optional SDK adapter with shared or explicit standalone mode. |
| `src/shake_bake/doctor.py` | Startup and metadata-only local-model checks. |
| `benchmarks/model_trial.py` | Checkpointed development trials and separate review scoring. |
| `src/shake_bake/routing.py` | Reviewed-record policy gates and model-choice explanation. |
| `src/shake_bake/gui.py` | Loopback workbench server and persistent job-owner thread. |
| `src/shake_bake/web/` | Responsive visual interface and published-model catalog. |
| `tests/` | Collection, selection, handoff and transport acceptance. |
| `examples/` | Inert demo and pinned-source receipts. |
| `benchmarks/evaluate_selection.py` | Synthetic retrieval smoke check. |
| `docs/` | Scope, research and qualification records. |
| `integration/mcp_smoke.py` | Pending SDK client qualification. |

Package metadata, entry points, MIT license and ignore rules remain in their normal locations. Historical receipts describe their stated earlier environments; [the import record](docs/import/2026-11-05.md) records this checkout's validation.

## Limits and next gates

Default search caps: 200 supported text files, 4,000 entries, eight directory levels, a cooperative five-second scan budget, four selected windows and 16 KiB of whole-line excerpts. Skips/cutoffs are disclosed. Selected files are re-read and compared with discovered hashes.

Up to two ranked windows per file preserve distant matching regions; one window per distinct file takes priority within the four-record cap. Further unmatched regions disclose a window cutoff. This does not guarantee complete code coverage. Task children use safe import settings and a trusted working directory, with task streams outside inspected roots.

Linux/POSIX is the development target; Windows remains refused pending an equivalent qualified boundary. This is not a hostile-filesystem or OS network sandbox. Trusted root ancestors, hard links, bind mounts, kernel stalls, complete secret detection and cross-file atomic snapshots remain limitations. Schema/reference checks do not prove a worker's semantic truth or immunity to prompt injection.

Persistent job storage, qualified MCP connections, direct cloud clients, patching and execution of inspected-project tests remain future work. [Model selection and tuning](docs/model-selection.md) compares published statistics for Qwen 9B/4B, Gemma 4 12B and a conditional gpt-oss 20B challenger; none has been measured here. [The next controlled trial](docs/next-trial.md) puts correct completed work ahead of savings. [Engineering references](docs/engineering-references.md) connect primary sources and book chapters to concrete decisions and checks.

[The native-capability study](docs/native-capability-study.md) compares existing ChatGPT/Codex and Claude features with the useful role of a local helper. The owner-controlled selector, `assist` CLI and local visual workbench are implemented. The setup wizard, automatic task classification, fully qualified host delivery, embeddings and vision input remain pending. No real profile has qualified for automatic selection. See [the visual workbench guide](docs/visual-workbench.md) and [the routing specification](docs/model-routing-and-usability.md).
