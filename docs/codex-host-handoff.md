# First actual Codex handoff

On November 5, 2026, an installed `0.4.0.dev7` helper completed one evidence-only handoff through `codex-cli 0.162.0-alpha.17.2` and official Python MCP SDK 2.3.0. This is an exposed synthetic integration check, not unseen accuracy, a private-source trial or a savings comparison. The sanitized [receipt](../examples/receipts/codex-host-smoke-2026-11-05.json) records its scope; raw events and account-related logs stay private and outside Git.

## What passed

The signed-in host used a temporary configuration exposing only the bundled `starter-demo`. Its seven completed tool calls:

1. Discovered only `starter-demo`, with Local AI paused.
2. Tried an unapproved project and received `project_not_permitted`.
3. Started one approved task with the original request copied exactly.
4. Retrieved its completed evidence-only result, with `final_answer_ready=false`, `requires_host_reasoning=true` and no worker invocation.
5. Fetched both captured source excerpts, matching their bytes, line ranges and hashes: 455 bytes total.
6. Cancelled the already completed task and received `DONE` again.

The request was: “Does validate_structure require the reported slice count to equal slices_detected? Give one concrete accepted mismatch and cite exact captured source lines.” The host correctly identified `validator.py:6` as accepting `len(reported_slices) <= slices_detected` and gave reported count 1 with detected count 2 as an accepted mismatch. The answer also cited the inert-demo note and explicitly reported no test execution. That answer was reviewed against the captured source; this small known-answer case is not a general semantic evaluator.

The local service survived host exit, remained paused, shut down cleanly, removed its private connection file and left the demo unchanged. No local model was called or downloaded. One accepted run took 29.002 seconds; this has no equivalent native-host baseline and establishes no efficiency improvement. Host-reported cumulative usage remains in the private run record. Cached input, billed usage and app-attributable overhead are not interchangeable; savings stay unknown. The exact hosted model was not pinned or independently established.

## Repeat explicitly

This command invokes a real cloud-backed assistant using its existing login and may consume account usage. It is never part of routine CI. Install the wheel and reviewed hash-locked optional SDK into an environment outside the checkout as described in [CONTRIBUTING.md](../CONTRIBUTING.md), and verify `codex login status` first. The harness is Linux-only and was checked with the CLI version above; a different CLI may refuse these options or produce an incompatible event schema.

From outside the checkout, with an absolute path to that installed environment and a **new** private output directory outside all inspected source:

```bash
env -u PYTHONPATH /absolute/sdk-env/bin/python -B \
  /absolute/checkout/integration/codex_host_smoke.py \
  --output /absolute/private-trials/codex-demo-01
```

The harness starts its own temporary local workbench with only the inert demo exposed. It uses ephemeral, read-only Codex execution, ignores normal user configuration, disables shell/apps/plugins/web/extra agents, and supplies only five allowlisted helper tools for this run. Existing authentication is reused without changing its home. No permanent host configuration is installed. The trace validator refuses other actions, incomplete tool calls, changed task identity, missing or altered source, incorrect mismatch counts, invalid citations, unsupported completion flags and failed turns. An incompatible event fails the check instead of being silently ignored.

The host deadline defaults to 120 seconds and may be set between 10 and 180 seconds. Timeout or interruption stops the harness's host process group; cleanup stops its own local service. Each run creates a private output directory and refuses to overwrite an earlier run. Treat raw events, stderr, settings and receipts as private: host startup context can contain local/account metadata. Do not publish these files wholesale. Offline tests validate fabricated synthetic traces without calling Codex; the saved actual trace was also revalidated after the final validation changes.

Earlier attempts remain in private records: task paraphrasing failed the exact-request check, and an experimental CLI flag produced an error event and failed validation. The flag was removed, rather than suppressing its warning. Those attempts are not counted as successful runs or comparable timing measurements.

## Active cancellation and recovery follow-up

Later on November 5, the same installed helper/SDK and Codex version completed an explicit `active-cancel` scenario. Its [separate sanitized receipt](../examples/receipts/codex-active-cancel-2026-11-05.json) records 14 tool calls, 455 captured source bytes and 48.222 seconds. This is a distinct synthetic run, with no timing baseline or savings claim.

The harness temporarily stops only the first bounded preparation child of its own temporary service. It checks the parent/child relationship and exact runner command and uses Linux pidfds to avoid signalling a reused PID. Package code, policy, source and model services are not patched. The gate makes a short evidence-only job remain active long enough to test cancellation; it is deliberate fault injection, not a naturally stalled model or a GPU-work cancellation test. An offline check also verifies an unrelated child is unaffected and a later preparation succeeds.

The actual host observed `RUNNING`, received `helper_busy` for a second start, and was refused evidence with `task_not_ready`. It cancelled the first task, observed `CANCELLED`, and was refused evidence from that cancelled task. It then completed the original permission-refusal and exact-source handoff sequence using a fresh task. The local check confirmed the cancelled runner exited and was reaped. The shared service remained paused, retained the cancelled and completed states, survived host exit and cleaned up normally.

Repeat explicitly with a new private output directory, under the same cloud/account and installation conditions above:

```bash
env -u PYTHONPATH /absolute/sdk-env/bin/python -B \
  /absolute/checkout/integration/codex_host_smoke.py \
  --scenario active-cancel \
  --output /absolute/private-trials/codex-cancel-01
```

The default scenario remains the original handoff. The cancellation scenario additionally requires Linux pidfd signalling and procfs in the same PID namespace as the process. The preflight compares `/proc/self/stat` with `os.getpid()` and verifies that the current process's main-thread `children` file is visible to the watcher's glob and readable before opening a pidfd, signalling, creating output or invoking the host. An empty children file is valid. A PID mismatch refuses with `runner_procfs_pid_namespace_mismatch`; missing/unreadable procfs refuses with `runner_procfs_unavailable`; hidden or unreadable child-process files refuse with `runner_procfs_children_unavailable`. The gate targets one owned runner and is cleaned up on exit. Offline checks cover synthetic trace acceptance, run configuration, prerequisite refusals and the real local process gate; none invokes Codex or a model. The process-gate test is explicitly skipped when its prerequisites are unavailable; that skip is not a successful cancellation check. On supported CI runners the real gate must still execute and pass.

## What comes next

INT-01 remains open. These runs did not exercise host disconnect/restart, deadlines under real model work, private-source handling, local Ollama plus host orchestration, or a guided user handoff. Active cancellation has evidence only for the explicitly stopped synthetic preparation runner. Claude Code was installed but signed out when inspected, so no actual Claude run occurred. Consumer ChatGPT needs its own supported connection and qualification; Codex login through ChatGPT does not prove that integration.

Recover and review the original exposed model-output receipts, extend actual-host disconnect/deadline/restart coverage, then freeze genuinely unseen source/tasks and independent review keys for the [paired comparison](next-trial.md). The two historical Qwen screening folders were not located in the checked owner workspace, parent folders or connected Drive during this follow-up; their scores remain unset. The committed `.dev2` receipts are evidence-only and cannot substitute for them. Keep native-host, deterministic-evidence and model-assisted arms separate. Do not promote a model or claim whole-task savings from these smoke checks.

Host configuration references: [official Codex MCP guide](https://developers.openai.com/codex/mcp/) and [configuration reference](https://developers.openai.com/codex/config-reference/), checked November 5, 2026 alongside installed CLI help. These document host options, not certification of this application.

## Separate final-answer diagnostic

The later [host-note comparison](host-note-diagnostic-2026-11-05.md) uses fresh
Codex sessions with identical captured evidence, with and without existing local
notes. It exercises no helper tools and performs no new local inference, so its
final-answer results do not qualify live model-assisted MCP orchestration,
disconnect/restart behavior or consumer ChatGPT integration.
