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

## What comes next

INT-01 remains open. This run did not exercise cancellation while work is active, host disconnect/restart, deadlines under real model work, private-source handling, local Ollama plus host orchestration, or a guided user handoff. Claude Code was installed but signed out when inspected, so no actual Claude run occurred. Consumer ChatGPT needs its own supported connection and qualification; Codex login through ChatGPT does not prove that integration.

Finish the existing exposed model-output reviews, extend actual-host failure/recovery coverage, then freeze genuinely unseen source/tasks and independent review keys for the [paired comparison](next-trial.md). Keep native-host, deterministic-evidence and model-assisted arms separate. Do not promote a model or claim whole-task savings from this smoke check.

Host configuration references: [official Codex MCP guide](https://developers.openai.com/codex/mcp/) and [configuration reference](https://developers.openai.com/codex/config-reference/), checked November 5, 2026 alongside installed CLI help. These document host options, not certification of this application.
