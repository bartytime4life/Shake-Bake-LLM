# Shake and Bake LLM Assistant

A standalone local preparation helper for Claude or ChatGPT, with an Ollama worker option. Ask a repository question and get a traceable source handoff. Claude or ChatGPT supplies the demanding judgment and final answer. The diagnostic evidence path needs no model, network connection or runtime package beyond Python 3.11+.

**Current source: `0.4.0.dev15`, built on the recovered standalone `0.4.0.dev4` package.** This replaces the separate `0.1.0.dev0` repository bootstrap while preserving it in Git history. The original runtime, tests, fixtures and technical documentation have been recovered; see the [import and publication review](docs/import/2026-11-05.md). This is a development preview, not a qualified production release.

| Status | Scope |
| --- | --- |
| Implemented | Exact evidence collection, bounded lexical retrieval, optional loopback Ollama preparation, local workbench, owner-record model gates, shared GUI/adapter job coordination, scoped project access and cancellation. |
| Verified in development | 204 offline program tests on the local PC; synthetic retrieval and ten exposed evidence-only Task Lab cases. Model-service tests use simulations. Official SDK 2.3.0 stdio/shared checks and actual Codex synthetic handoff/cancellation checks passed. |
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

The [focused workbench fixes](docs/workbench-fixes-2026-11-05.md) confirm Local AI changes before allowing new work, protect the selected brief from delayed responses, add connection retry, and improve mobile history and keyboard source scrolling. [Startup restoration](docs/startup-brief-recovery-2026-11-05.md) also respects newer results and leaves task controls and polling available while old evidence loads. Status messages stay beside the task controls without covering them. Wider accessibility and real-model qualification remain open.

The [request-recovery follow-up](docs/request-recovery-2026-11-05.md) bounds stalled browser requests, checks session state after an uncertain task start and restores connection status during active-job polling. If a start response is lost, check Recent briefs before starting again; the app does not automatically repeat the task.

[Draft recovery](docs/draft-context-2026-11-05.md) restores the request with its saved project and task type. An unavailable saved choice requires an explicit replacement before preparation. Text entered during connection is preserved, and a visible status reports browser saving failures.

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

This opens the loopback-only browser interface at `http://127.0.0.1:8421`. Describe the task, choose an approved project and select **Prepare brief**. The graphite/amber workbench keeps task type and optional Local AI controls under **Options**; no model installation or setting change is needed for the evidence-only demo. Recent briefs, captured source, model details and exports remain available on demand. Published benchmarks and owner-recorded local trials have separate labels.

Opening `src/shake_bake/web/index.html` directly shows a launch guide. Use the running local address to prepare evidence; opening the page file does not start the service. See [file-opening recovery and check boundaries](docs/file-launch-recovery-2026-11-05.md).

Add an approved source folder at launch with `--project my-project=/absolute/project/folder`; choose it from the interface. Use `--policy /absolute/path/outside-the-project/routing.json` for an owner policy. `--no-browser` starts the service without opening a browser; `--port 8422` selects a different local port. Installed packages also provide `shake-bake-ui`.

The offline preview is a **recorded demo inspector**, with synthetic source and no model inference. It is a separate export; it does not run new jobs. Read [the workbench guide](docs/visual-workbench.md) for scope and setup. Current local Chrome interaction and comparison evidence is in [design-qa.md](design-qa.md). The earlier blocked cloud-browser attempt remains historical; current checks do not establish a formal accessibility audit.

### Continue in Claude or ChatGPT

After preparing, review the source and select **Copy brief**, then paste/send it in Claude or ChatGPT. The nearby links can open either assistant; choosing a destination in Shake & Bake is unnecessary. The brief includes your original request, exact evidence, gaps and instructions for the assistant. With Local AI on, the local model (the "intern") drafts the prompt the assistant reads first: a goal, the evidence to read first, the questions to answer and a suggested approach, labeled unverified and placed ahead of the fixed instructions. See [the handoff-prompt record](docs/handoff-prompt-2026-11-06.md). **Review & export** provides selectable text, **Save brief as .txt** and JSON export. Nothing is sent automatically. See [the handoff guide and check boundaries](docs/assistant-handoff.md).

Start with evidence-only or **Best tested**; the shipped candidate profiles do not qualify for automatic model use. To enable an explicit diagnostic candidate trial on inert source:

```bash
./scripts/run-workbench --allow-candidate-trials
```

Under **Options → Model details**, refresh installed models, choose **Try a candidate — unqualified**, select a pinned installed model and acknowledge the trial. No download or daemon start occurs. Model selection preferences persist in this browser; the shared service saves the Local AI choice. Jobs and captured results remain session-only. The owner launch flag and enabled routing policy are required. Candidate runs never promote profiles.

Under **Options → Model details**, expand **This computer & selected model** for explicit readiness checks. Computer observations need no Ollama call; the selected-model check needs Local AI on and reads metadata only. Unknown GPU memory, actual model fit and task accuracy stay unknown. Worker notes now retain runtime/settings and receive actual scan cutoffs. A runtime change discards notes while preserving source. See [readiness and screening results](docs/validation-0.4.0.dev6.md).

## Prepare a real model trial

Fresh [owner-PC screening](docs/screening-2026-11-05.md) now has retained records: Qwen 3.5 4B timed out on the first case; Qwen 3 1.7B completed ten exposed cases but only four handoffs met the disclosed assistant-review rubric. Exact source survived, while the notes still missed or misread decisive facts. All profiles remain unqualified. These new runs do not reconstruct the missing historical screening or establish unseen accuracy or savings. A [follow-up prompt experiment](docs/validation-0.4.0.dev8.md) also met the rubric on only four cases and increased unsupported claims; that prompt was rejected and reverted. The shipped worker now refuses models whose declared thinking controls cannot honor its `think: false` request, before transmitting source. Missing controls remain unknown; they do not establish compatibility or accuracy.

The November 6 [handoff-prompt runs](docs/handoff-prompt-2026-11-06.md) completed all ten exposed cases with Qwen 3 8B and Qwen 3.5 4B under the new design, with an author-only read of the drafts; they are development evidence, not qualification. Read [current evaluation status](docs/evaluation-status.md) for the complete sequence of retained trials. The latest [four-arm thinking-budget comparison](docs/thinking-budget-2026-11-05.md) ran forty attempts: thinking off at 512 tokens produced 6/10 supported handoffs; thinking on produced 3/10 at 512 and 6/10 at both 1,024 and 2,048. Each larger budget still truncated the concurrency case and retained two critical unsupported claims, so both were rejected. These private diagnostics do not change the shipped thinking-off, 512-token worker or add GUI/CLI budget controls.

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

That model is an example, not a detected installation. The client checks `/api/show` before sending source and refuses known cloud names and reported remote models. It ignores proxy/host environment variables and follows no redirects. A shared 30-second deadline, bounded responses, a 6,000-byte source-message cap plus a separately budgeted instruction prompt, 1,024 generated tokens and an 8,192-token requested context bound preparation. Add `--task-kind` to pass a hint to the drafted prompt.

Configure the trusted Ollama daemon with cloud features disabled first: [official guidance](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features). Ollama documents `OLLAMA_NO_CLOUD=1` or its daemon configuration setting, followed by a restart. Setting a variable on this client does not reconfigure an existing server. The client cannot attest model weights, enforce the daemon's network policy, prove every custom template fits, or guarantee GPU-work cancellation after disconnect.

The worker returns the `handoff_prompt_v1` structure: goal, focus, asks, approach, notes, references and open questions. The brief renders the draft as a fenced, labeled prompt section ahead of the exact evidence; a model that omits the draft falls back to notes only. Everything stays labeled unverified. Unknown references, added fields, tool calls, duplicate JSON keys, truncated replies and model mismatches are refused. Every selected source remains visible. Worker failure retains evidence and returns `ABSTAIN`.

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

The current candidate passed 196 offline program tests on the local PC, including six for the drafted handoff prompt, six for controlling-context collection, three for BM25-style scoring with the distractor exclusion, three for the external file-recall adapter, one for the brief's answer section, one for the off-by-default datamarked worker input four for the optional embedding rerank against a loopback stub, one for crafted filenames staying inside inline code and two for the matched-line index. The recovered tests remain, with coverage for candidate boundaries, capability observations, wire/receipt settings, runtime drift and worker-visible collection limits; twelve additional tests cover synthetic host-trace acceptance, configuration and the owned-runner cancellation gate. Three worker compatibility tests verify refusal before source transmission and exact-evidence retention; five later tests cover process-gate prerequisites. See the [local PC validation](docs/pc-readiness-2026-11-05.md), [worker validation](docs/validation-0.4.0.dev8.md), [previous runtime validation](docs/validation-0.4.0.dev7.md) and [host validation](docs/codex-host-handoff.md). HTTP model tests use a simulated loopback service, not a real model; GUI tests exercise the actual loopback HTTP server and real bounded preparation children. Routing tests use explicitly fabricated qualification records. The task lab supplies ten exposed jobs with independent grading keys outside each fixture root. All ten retain their required source spans on the diagnostic path. This is mechanical evidence coverage, not model accuracy. The saved previous candidate retained the required spans in nine of ten cases; the distant-condition case motivated the two-window retrieval change.

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

Development update (November 7, line index): `0.4.0.dev15` lists, after the file map, the request-term matches that no excerpt covers, as line numbers with short texts (six files, twelve lines each, 2,048 bytes, each cutoff disclosed), so a host can ask for a range instead of reading or searching a large file. On the log comparison fixture the brief now carries the second failing test at line 1805 that the excerpts missed, and on the publish fixture the contract sentence that was previously only mapped; briefs grew by 540 to 910 bytes. Texts are untrusted repository strings in inline code. See [the line-index record](docs/line-index-2026-11-07.md).

Development update (November 7, hardening): a review of the Markdown handoff found that repository paths and map first-lines were rendered as plain text outside fences, so a crafted filename could read as a heading or an instruction, and that chat clients may normalize carriage returns inside fenced text. `0.4.0.dev14` renders those strings as inline code with a safe backtick run and escaped control characters, refuses paths containing control characters at the collector, notes carriage returns per excerpt and points to the JSON download as the exact-bytes path (BUG-019). Covered by a crafted-filename clipboard test and a Python test; real-Chrome suites pass.

Development update (November 7, rerank): `0.4.0.dev14` adds an optional embedding rerank of candidate windows: `--rerank-model` on the CLI brief, the Task Lab runner and the recall adapter asks an installed loopback Ollama embedding model to score the top 24 lexical candidates against the request and reorders them before primary selection, adding no window, refusing remote or mismatched responses, and falling back to lexical order with the refusal recorded. No embedding model is installed on the owner's PC, so no trial is recorded; four tests cover the mechanism with a loopback stub. See [the embedding-rerank record](docs/embedding-rerank-2026-11-07.md).

Development update (November 7, experiment): `0.4.0.dev13` adds an off-by-default datamarking option for the local worker's copy of excerpt text (a marker in place of each space, Spotlighting-style) and a `--datamark` Task Lab flag, then records a negative result: on the ten exposed cases Qwen 3 8B still drafted an approach that follows the injected source instruction, Qwen 3.5 4B stayed correct with or without the marker, no marker leaked, and generated tokens rose about six percent. The flag stays off; see [the datamarking record](docs/datamark-2026-11-07.md).

Development update (November 7, later): `0.4.0.dev12` makes the copied brief a Markdown message Claude or ChatGPT can read directly: the request and what to answer first, the ground rules, each exact excerpt as a fenced code block headed by its id, path, line range and hash, the file map, scan limits in plain words, and the verbatim JSON request and evidence identities last for verification. The starter-demo brief went from 4,334 to 3,375 bytes and from 100 to 57 lines; the page now shows the brief's size with a bytes/4 token estimate. The CLI brief gains the same "Answer with" section. Clipboard, real-Chrome and Python checks pass; see [the handoff-format record](docs/handoff-format-2026-11-07.md).

Development update (November 7): `0.4.0.dev11` scores matching files BM25-style (rarer request terms weigh more, repeated hits saturate, no length normalization) and excludes files whose only hits are widespread terms as `low_signal_match`, both disclosed in the scan receipt. The ten exposed Task Lab cases keep all required spans; on the four comparison fixtures the log case now excerpts its two test files instead of a utility file and drops eighteen utility files from the map. A new `benchmarks/external_recall.py` reports file-level recall of the collector on externally authored localization cases (no model, no host); a development smoke on twelve of this repository's own commits moved mean excerpt recall from 10.7% to 18.6%. See [the retrieval-scoring record](docs/retrieval-scoring-2026-11-07.md).

Development update (November 6, later): `0.4.0.dev10` follows the four primary excerpts with bounded controlling context: the top-level definitions they reference, one use of a name they define, one test file naming them, and a map of matched files not excerpted, each labeled with its mechanical reason. On the four exposed comparison fixtures, decisive-file coverage rose from 15/25 to 23/25 excerpted and the largest brief grew to about 1,270 tokens; whether a host then takes fewer turns is untested. See [the controlling-context record](docs/controlling-context-2026-11-06.md) and [the host context cost analysis](docs/host-context-cost-2026-11-06.md) that motivated it.

Development update (November 6): `0.4.0.dev9` makes the local worker draft the assistant-facing prompt (`handoff_prompt_v1`, 1,024 requested output tokens) and records ten-case runs of Qwen 3 8B and Qwen 3.5 4B plus a pre-source refusal of Qwen 3 4B; see [the handoff-prompt record](docs/handoff-prompt-2026-11-06.md). The preceding `.dev8` adds a worker compatibility guard and records a rejected prompt experiment. See [validation and remaining gates](docs/validation-0.4.0.dev8.md). The preceding `.dev7` adds saved Local AI settings, a supported-Python source launcher and external evaluation dataset support. Historical `.dev5`/`.dev6` model and browser observations retain their original scope.
