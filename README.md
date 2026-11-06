# Shake and Bake LLM Assistant

A standalone local preparation helper for Claude or ChatGPT, with an Ollama worker option. Ask a repository question and get a traceable source handoff. Claude or ChatGPT supplies the demanding judgment and final answer. The diagnostic evidence path needs no model, network connection or runtime package beyond Python 3.11+.

**Current source: `0.4.0.dev8`, built on the recovered standalone `0.4.0.dev4` package.** This replaces the separate `0.1.0.dev0` repository bootstrap while preserving it in Git history. The original runtime, tests, fixtures and technical documentation have been recovered; see the [import and publication review](docs/import/2026-11-05.md). This is a development preview, not a qualified production release.

| Status | Scope |
| --- | --- |
| Implemented | Exact evidence collection, bounded lexical retrieval, optional loopback Ollama preparation, local workbench, owner-record model gates, shared GUI/adapter job coordination, scoped project access and cancellation. |
| Verified in development | 176 offline program tests on the local PC; synthetic retrieval and ten exposed evidence-only Task Lab cases. Model-service tests use simulations. Official SDK 2.3.0 stdio/shared checks and actual Codex synthetic handoff/cancellation checks passed. |
| Partially qualified | The [Codex smoke checks](docs/codex-host-handoff.md) cover an exposed synthetic task and cancellation of an explicitly stopped owned runner followed by a fresh successful task. Actual Claude/consumer ChatGPT, disconnect/deadline/restart, model-assisted host orchestration and private-source handoffs remain unqualified. |
| Planned | Guided setup, automatic per-PC calibration, persistent profiles, durable job recovery and direct cloud-provider clients. Local AI on/off persistence is implemented. |
| Unverified or unmeasured | Full owner-PC workflows, unseen final-host model accuracy, controlled runtime performance and peak memory, broader host delivery, wider accessibility/device qualification, Windows support, independent security qualification and whole-task cloud savings. |

## Get the source

```bash
git clone https://github.com/bartytime4life/Shake-Bake-LLM.git
cd Shake-Bake-LLM
./scripts/run-workbench --help
```

Use Linux and Python 3.11+ for development. Run the model-free demo below before approving any real source. For reproducible core tests, wheel installation and optional SDK checks, follow [CONTRIBUTING.md](CONTRIBUTING.md). No model weights or third-party runtime distributions are bundled.

The [documentation guide](docs/README.md) separates current instructions from dated experiments, acceptance records and research. The [prioritized to-do list](TODO.md) puts real-machine/model accuracy, host delegation and measured benefit first. Every pending item has a completion check; the [PC checklist](docs/PC-CHECKLIST.md) supplies the detailed runbook.

The [whole-workflow UX plan](docs/UX-WORKFLOW.md) connects first setup, shared job/policy state, local preparation, evidence review, handoff and recovery. It records current code-level gaps and planned implementation slices; browser/user-flow qualification remains pending.

The [focused workbench fixes](docs/workbench-fixes-2026-11-05.md) confirm Local AI changes before allowing new work, protect the selected brief from delayed responses, add connection retry, and improve mobile history and keyboard source scrolling. Status messages stay beside the task controls without covering them. Wider accessibility and real-model qualification remain open.

The [local PC readiness walkthrough](docs/pc-readiness-2026-11-05.md) verifies installed-package identity, real model metadata and selected in-app-browser flows. It also corrects a refresh message that stayed in progress after completion. That walkthrough was metadata-only. The [subsequent copy and screening review](docs/copy-and-screening-2026-11-05.md) adds persistent copy status and selectable exact handoff text, and records a cloud-disabled Qwen 3 8B run: six of ten exposed handoffs met the assistant-review rubric. A final installed synthetic brief passed both native and manual clipboard readback; independent accuracy and wider browser qualification remain open.

Shake and Bake is a standalone app with its own configuration, test fixtures and data. Its bundled code evaluations use self-contained synthetic projects; no other application is required.

The original app uses the existing [MIT license](LICENSE), which permits commercial reuse and resale with its required notice retained. External dependencies and model weights have separate terms. Read [the licensing plan](docs/LICENSING.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [model-license registry](MODEL_LICENSES.json). Exact model-artifact redistribution review remains pending. Building a wheel requires setuptools 77+; running the source app adds no runtime dependency.

Before release or feature promotion, review [Known Issues and release expectations](KNOWN_ISSUES.md) and the security/bug gates in the [PC checklist](docs/PC-CHECKLIST.md). Unverified security, accuracy and integration checks remain pending; the program-test count is not a security certification.

The local web server now caps active connections, expires stalled requests and cancels expired queued operations. See [connection limits and regression evidence](docs/connection-limits.md); broader load/security qualification remains pending.

## Shared GUI and assistant work

The [shared-coordinator guide](docs/shared-coordinator.md) connects the workbench and prepared adapter to the same routed jobs, captured evidence and session pause state. Private connection files and explicit project scopes are tested. The interface adds first-run help, job-origin labels and pinned completed-result identity. One actual Codex evidence-only handoff now has [scoped evidence and a repeatable check](docs/codex-host-handoff.md); broader host qualification remains pending. SDK/browser development checks are recorded separately in [validation](docs/validation-0.4.0.dev6.md).

## Open the visual workbench

On Linux, from the extracted `shake-and-bake` folder:

```bash
./scripts/run-workbench
```

The launcher chooses an installed Python 3.11+ even when the system `python3` is older. New launches start with Local AI off until explicitly enabled; that choice is saved in private local state across restarts. See [saved preference boundaries](docs/local-ai-preferences.md). Starting a task never resumes a paused service.

This opens the loopback-only browser interface at `http://127.0.0.1:8421`. The owner-selected graphite/amber interface includes a bundled inert demo, task choices, paired source excerpts, expandable model details, pinned request/job identity, copy/JSON export and a local-AI off switch. No model installation is needed for the evidence-only demo. Published benchmarks and owner-recorded local trials have separate labels.

Add an approved source folder at launch with `--project my-project=/absolute/project/folder`; choose it from the interface. Use `--policy /absolute/path/outside-the-project/routing.json` for an owner policy. `--no-browser` starts the service without opening a browser; `--port 8422` selects a different local port. Installed packages also provide `shake-bake-ui`.

The offline preview is a **recorded demo inspector**, with synthetic source and no model inference. It is a separate export; it does not run new jobs. Read [the workbench guide](docs/visual-workbench.md) for scope and setup. Current local Chrome interaction and comparison evidence is in [design-qa.md](design-qa.md). The earlier blocked cloud-browser attempt remains historical; current checks do not establish a formal accessibility audit.

Start with evidence-only or **Best tested**; the shipped candidate profiles do not qualify for automatic model use. To enable an explicit diagnostic candidate trial on inert source:

```bash
./scripts/run-workbench --allow-candidate-trials
```

In Model details, refresh installed models, choose **Try a candidate — unqualified**, select a pinned installed model and acknowledge the trial. No download or daemon start occurs. Model selection preferences persist in this browser; the shared service saves the Local AI choice. Jobs and captured results remain session-only. The owner launch flag and enabled routing policy are required. Candidate runs never promote profiles.

In Model details, expand **This computer & selected model** for explicit readiness checks. Computer observations need no Ollama call; the selected-model check needs Local AI on and reads metadata only. Unknown GPU memory, actual model fit and task accuracy stay unknown. Worker notes now retain runtime/settings and receive actual scan cutoffs. A runtime change discards notes while preserving source. See [readiness and screening results](docs/validation-0.4.0.dev6.md).

## Prepare a real model trial

Fresh [owner-PC screening](docs/screening-2026-11-05.md) now has retained records: Qwen 3.5 4B timed out on the first case; Qwen 3 1.7B completed ten exposed cases but only four handoffs met the disclosed assistant-review rubric. Exact source survived, while the notes still missed or misread decisive facts. All profiles remain unqualified. These new runs do not reconstruct the missing historical screening or establish unseen accuracy or savings. A [follow-up prompt experiment](docs/validation-0.4.0.dev8.md) also met the rubric on only four cases and increased unsupported claims; that prompt was rejected and reverted. The shipped worker now refuses models whose declared thinking controls cannot honor its `think: false` request, before transmitting source. Missing controls remain unknown; they do not establish compatibility or accuracy.

Read [current evaluation status](docs/evaluation-status.md) for the complete sequence of retained trials. The latest [four-arm thinking-budget comparison](docs/thinking-budget-2026-11-05.md) ran forty attempts: thinking off at 512 tokens produced 6/10 supported handoffs; thinking on produced 3/10 at 512 and 6/10 at both 1,024 and 2,048. Each larger budget still truncated the concurrency case and retained two critical unsupported claims, so both were rejected. These private diagnostics do not change the shipped thinking-off, 512-token worker or add GUI/CLI budget controls.

The separate [host-note diagnostic](docs/host-note-diagnostic-2026-11-05.md) completed twenty final answers: evidence alone met the rubric on 9/10 cases, versus 8/10 with the same evidence plus existing local notes. Both avoided counted false claims, but the assisted arm lost a required uncertainty. The no-regression gate failed; this does not establish a useful local-model contribution or whole-task savings.

The subsequent [native-retrieval comparison](docs/native-preparation-2026-11-05.md) tested four larger synthetic projects twice per condition. Native search and the same tools plus deterministic preparation both met the rubric on 8/8 answers. Preparation used 24.35% fewer reported input tokens but had an 8.03% slower median timed workflow; the predeclared efficiency signal failed. One initial setup failure and all sixteen corrected attempts are retained. No local model was used, and these exposed cases do not establish whole-task savings.

The [earlier frozen-prompt comparison](docs/reasoning-screening-2026-11-05.md) includes a separately authored cohort with 2/10 supported original handoffs and 3/10 experimental handoffs. That cohort is now exposed and must not be reused as unseen. [External datasets](docs/held-out-evaluation.md) support pinned inputs and isolated grading keys; independent human qualification and representative native-host benefit qualification remain open.

Start with the [Run on your PC checklist](docs/PC-CHECKLIST.md). Every owner-PC item stays unchecked until actually verified there.

The [per-PC calibration plan](docs/per-pc-calibration.md) and [Your computer & tuning GUI design](docs/per-pc-calibration-ui.md) explain the next hardware-aware milestone. Automatic tuning and that new dashboard remain planned.

The startup check and repeatable trial runner are ready. They record reported model identity, settings, source integrity, per-attempt failures and a separate grading sheet. Accuracy stays unset until review. Start with the [PC readiness and trial guide](docs/pc-readiness-and-trials.md). The [open-gap review](docs/open-gaps.md) records what still needs proving, including representative native-host benefit and actual hardware behavior. No trial automatically promotes a model.

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

The optional `mcp` extra and `shake-bake-mcp` entry point provide an official-SDK stdio adapter. The installed official SDK 2.3.0 stdio/shared replay is recorded in [validation](docs/validation-0.4.0.dev6.md), and the first actual Codex check in [host handoff](docs/codex-host-handoff.md). Actual Claude/consumer ChatGPT connections remain unqualified. See [helper-contract.md](docs/helper-contract.md) for the five methods, launch command and qualification gate. The SDK and live-host scripts are separate from the offline base suite; the live cloud check is opt-in and never runs in CI.

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

The current candidate passed 176 offline program tests on the local PC. The recovered tests remain, with coverage for candidate boundaries, capability observations, wire/receipt settings, runtime drift and worker-visible collection limits; twelve additional tests cover synthetic host-trace acceptance, configuration and the owned-runner cancellation gate. Three worker compatibility tests verify refusal before source transmission and exact-evidence retention; five later tests cover process-gate prerequisites. See the [local PC validation](docs/pc-readiness-2026-11-05.md), [worker validation](docs/validation-0.4.0.dev8.md), [previous runtime validation](docs/validation-0.4.0.dev7.md) and [host validation](docs/codex-host-handoff.md). HTTP model tests use a simulated loopback service, not a real model; GUI tests exercise the actual loopback HTTP server and real bounded preparation children. Routing tests use explicitly fabricated qualification records. The task lab supplies ten exposed jobs with independent grading keys outside each fixture root. All ten retain their required source spans on the diagnostic path. This is mechanical evidence coverage, not model accuracy. The saved previous candidate retained the required spans in nine of ten cases; the distant-condition case motivated the two-window retrieval change.

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
| `integration/mcp_smoke.py` | Optional SDK compatibility checks; actual-host qualification is separate. |

Package metadata, entry points, MIT license and ignore rules remain in their normal locations. Historical receipts describe their stated earlier environments; [the import record](docs/import/2026-11-05.md) records this checkout's validation.

## Limits and next gates

Default search caps: 200 supported text files, 4,000 entries, eight directory levels, a cooperative five-second scan budget, four selected windows and 16 KiB of whole-line excerpts. Skips/cutoffs are disclosed. Selected files are re-read and compared with discovered hashes.

Up to two ranked windows per file preserve distant matching regions; one window per distinct file takes priority within the four-record cap. Further unmatched regions disclose a window cutoff. This does not guarantee complete code coverage. Task children use safe import settings and a trusted working directory, with task streams outside inspected roots.

Linux/POSIX is the development target; Windows remains refused pending an equivalent qualified boundary. This is not a hostile-filesystem or OS network sandbox. Trusted root ancestors, hard links, bind mounts, kernel stalls, complete secret detection and cross-file atomic snapshots remain limitations. Schema/reference checks do not prove a worker's semantic truth or immunity to prompt injection.

Persistent job storage, qualified MCP connections, direct cloud clients, patching and execution of inspected-project tests remain future work. [Model selection and tuning](docs/model-selection.md) compares published statistics for Qwen 9B/4B, Gemma 4 12B and a conditional gpt-oss 20B challenger; none has been measured here. [The next controlled trial](docs/next-trial.md) puts correct completed work ahead of savings. [Engineering references](docs/engineering-references.md) connect primary sources and book chapters to concrete decisions and checks.

[The native-capability study](docs/native-capability-study.md) compares existing ChatGPT/Codex and Claude features with the useful role of a local helper. The owner-controlled selector, `assist` CLI and local visual workbench are implemented. The setup wizard, automatic task classification, fully qualified host delivery, embeddings and vision input remain pending. No real profile has qualified for automatic selection. See [the visual workbench guide](docs/visual-workbench.md) and [the routing specification](docs/model-routing-and-usability.md).

Development update (November 5): `0.4.0.dev8` adds a worker compatibility guard and records a rejected prompt experiment. See [validation and remaining gates](docs/validation-0.4.0.dev8.md). The preceding `.dev7` adds saved Local AI settings, a supported-Python source launcher and external evaluation dataset support. Historical `.dev5`/`.dev6` model and browser observations retain their original scope.
