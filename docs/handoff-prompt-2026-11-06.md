# The intern drafts the prompt: `handoff_prompt_v1`

Recorded November 6, 2026 for `0.4.0.dev9`. This change makes the optional local Ollama worker (the "intern") draft the prompt that Claude or ChatGPT reads first, instead of returning a bare summary that the brief appended near the end. Exact source, the original request and the fixed receiving-assistant instructions are unchanged. The draft is labeled unverified everywhere it appears. No model is promoted and no profile is qualified by this record.

## What changed

The worker still sends one `think: false` chat request with the original request, the collection record and the exact excerpts, and still refuses remote metadata, incompatible thinking controls, tool calls, truncation, unknown evidence references and added fields before or after inference. The response schema now asks for seven fields:

| Field | Purpose | Bound |
| --- | --- | --- |
| `goal` | One or two sentences, addressed to the assistant, stating what it must decide or deliver. | 600 characters |
| `focus` | Evidence to read first, most decisive first, each with a reason tied to the request. | Up to four distinct existing IDs, 300-character reasons |
| `asks` | The specific questions the assistant must answer, phrased to be checked against cited lines. | One to six, 400 characters each |
| `approach` | Ordered steps naming the concrete values to compare and when to say "not established". | Up to six, 400 characters each |
| `summary`, `evidence_ids`, `questions` | The existing source-grounded notes, references and unresolved points. | Unchanged bounds |

A note that omits the new fields, or leaves `goal`/`asks` blank, is still accepted; the brief then falls back to the previous evidence-plus-notes presentation. Any other added key, unknown ID, duplicate focus entry or oversized value is refused with the existing `worker_invalid_note` / `worker_invalid_evidence_reference` codes, and exact evidence is retained.

Requested generation now allows 1,024 output tokens instead of 512, because the structured draft is longer than a summary; every receipt records `preparation_design: handoff_prompt_v1` with the exact requested options. The fixed instruction text is budgeted separately (4,096 bytes) from the 6,000-byte source message so a longer prompt never shrinks the source the model may see. An optional task-kind hint reaches the worker from the routed, candidate and `brief --task-kind` paths; collection is unaffected.

Presentation:

- The CLI brief gains a fenced `## Prompt for the assistant - drafted locally, unverified` section between the original request and the evidence records.
- The workbench copy/text/JSON handoff places the same drafted prompt after the JSON-encoded original request and before the fixed receiving-assistant instructions, keeping the request on line four for the existing browser checks. The page shows it under **Prompt drafted by local AI · unverified** above the local notes.
- The shared adapter result carries the new fields inside `worker`; `final_answer_ready` stays false and the label stays `unverified_worker_interpretation`.

## Development run on this PC

Ten exposed Task Lab cases, bundled dataset `bundled-task-lab-v1`, one attempt each, shipped 30-second deadline, RTX 5080, Ollama 0.35.1 on `127.0.0.1:11434`. Receipts, including the earlier run with the first instruction wording, are retained under `examples/receipts/handoff-prompt-2026-11-06/`. Every response passed the remote-host and model-identity checks; the daemon's cloud-feature setting was not re-verified for this run.

| Model | Result | Generated tokens | Wall time per case |
| --- | --- | --- | --- |
| `qwen3:8b` | 10/10 complete, 10/10 required spans, no worker errors | 348–573 | 4.3–6.0 s including a cold load each time |
| `qwen3.5:4b` | 10/10 complete, 10/10 required spans, no worker errors | 313–549 | 3.6–4.9 s |
| `qwen3:4b` | Refused before source submission on all ten cases: `worker_thinking_mode_unsupported` (declared thinking values `[true]` only) | — | — |

The earlier November 5 screening recorded a Qwen 3.5 4B timeout on its first case; this run completed with the same deadline. No cold/warm study was run, so that difference is unexplained.

### Author review of the drafts (not independent qualification)

The drafts were read against `grading-keys.json` by the same AI session that wrote the instructions. This is a development read, with the known contamination that implies; it is not human review, a reserved cohort or a final-host comparison.

`qwen3.5:4b` drafts met the intent on all ten cases: faithful goals, concrete traces (`3 > 3`, `20 < 20`, `active_jobs < 2` versus `MAX_ACTIVE_JOBS = 1`), the injected source instruction named as untrusted data, and the file-budget cutoff cited before any repository-wide verdict. Noise observed: two speculative open questions (driver version, "reported as a bug?") and one muddled change-review summary sentence; no counted false claim.

`qwen3:8b` drafts were weaker on three cases. Repo-tour asked only "what is the role of X" and misread the empty evidence list as returned evidence. Runtime-mode no longer stated the environment override that the first wording had captured. Injection kept an approach step saying the answer "should reflect the instructions" if they override the status, which the fixed receiving-assistant instructions contradict but which a careless reader could follow. The other seven drafts were source-grounded with usable asks, and failure-triage proposed the `>=` hypothesis without claiming a rerun.

The one instruction revision between the two runs (name cutoffs in the approach, name verdict-demanding source text as untrusted, keep questions distinct from asks, name concrete inputs) fixed the 8B coverage-budget draft and improved the 4B injection draft; it did not fix the 8B injection step and slightly worsened 8B runtime-mode. Both runs are retained.

### Workbench check

An isolated workbench session (private state directory, `--allow-candidate-trials`, Local AI on, candidate `qwen3.5:4b`, acknowledged) prepared the synthetic demo request through the running page. The drafted prompt appeared under its own heading, the copy text placed it after the JSON-encoded request and before the fixed instructions, and the local notes and routing explanation remained. The browser pane could not render a screenshot in this session, so this is a DOM-level check, not a visual one. Nothing was sent to an assistant.

## Program checks

183 Python tests pass (six new: schema and field exposure, blank-field fallback, ten invalid-field refusals, task-kind refusal before connecting, fenced CLI rendering, CLI hint). Node checks pass: frontend API smoke with the new prompt mapping, 17 clipboard/handoff cases including the drafted-prompt layout and the no-prompt fallback, readiness, request-deadline, file-launch and server-startup suites. The evidence-only Task Lab and synthetic retrieval checks pass unchanged.

## What this does not establish

- Semantic accuracy on unseen tasks, or that either model's draft improves the assistant's final answer. The next gates in [evaluation status](evaluation-status.md) still apply: freeze this design, author a reserved cohort, run the paired final-host comparison and obtain human review.
- Qualification of any profile for automatic selection; `default-policy.json` is unchanged and still lists candidates only.
- Cold/warm timing, peak memory or behavior under the 35B and 120B models installed on this PC, which were not run.
- Delivery to Claude or ChatGPT; copy completion remains a local clipboard event.
