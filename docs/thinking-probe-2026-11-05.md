# Thinking mode at the existing limits — November 5, 2026

The installed Qwen 3 8B model produced a complete final JSON response on only
**three of ten known cases with thinking enabled**. Seven responses ended with
`done_reason=length` at the requested 512-token cap. All ten thinking-off responses
completed. This configuration fails the frozen completion gate; the application
settings and acceptance rules remain unchanged.

This follows the [rejected prompt experiment](reasoning-screening-2026-11-05.md).
That experiment exposed reasoning failures even when the supplied source was
complete. The next diagnostic changed only the submitted `think` field, holding
the current production prompt, exact source, schema and other request fields
constant. No new model was downloaded and no unseen cohort was reused for tuning.

## Design and identity

The ten bundled development cases remain known and exposed. One attempt per case
per mode gave twenty requests. Seed 17 shuffled case order; which mode ran first
alternated by case. No generation seed was supplied. Both modes requested
temperature 0, 512 output tokens, 8,192 context tokens, `keep_alive=0` and
`stream=false`, with the existing 30-second deadline, 6,000-byte message cap and
262,144-byte response cap. There were no retries or limit increases.

The private probe captured each exact outgoing request from the installed worker
before chat transport, then froze all ten payloads before the first generation.
For each pair, software verified that removing only `think` made the two request
objects equal. Grading keys stayed outside fixture roots and were not sent to the
model. Source hashes, dataset identity, model metadata, reported digest and runtime
were checked throughout. No source, system prompt, application or policy file was
changed to run this diagnostic.

The model reported `qwen3:8b`, Q4_K_M, digest
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`,
with Ollama `0.35.1`. Its metadata explicitly listed both boolean thinking modes.
The installed production pipeline was
`3beaa7d1618112b9f5b5c76f4aac07eec897ab3b7b6d9a545d3c5c70ae663b09`.
The receipt separately pins the private probe code; that probe is not a new
production pipeline or a qualified model profile.

Ollama documents `think` controls and separates the thinking and final-content
fields in a chat response. See the [thinking documentation](https://docs.ollama.com/capabilities/thinking)
and [chat API](https://docs.ollama.com/api/chat). These documents support the request
shape; the completion and correctness results here come from the actual local run.

## Completion and separate review

| Mode | Requests completed at transport | Complete final JSON | Truncated responses | Accepted by unchanged production validator |
| --- | ---: | ---: | ---: | ---: |
| Thinking off | 10/10 | 10/10 | 0 | 10/10 |
| Thinking on | 10/10 | 3/10 | 7 | 0/10 |

The three complete thinking-on results were coverage-budget, boundary and
distant-contradiction. Repository-tour, failed-test triage, change review,
unknown hardware, concurrency, source injection and runtime mode were truncated.
Five truncated responses had no final content; two contained partial content.
None was repaired, retried or accepted as a complete handoff.

The current production validator intentionally refuses a nonempty thinking field.
To evaluate the final content separately, the private probe retained the original
bounded response and replayed a copy with only that field omitted through the
unchanged validator, without a network call. This diagnostic projection still
rejects truncation, tools, remote/model mismatches, malformed JSON, unknown evidence
references and invalid usage. It is explicitly **not production acceptance**.
Raw partial responses and local reasoning remain private; only validated final
content is supplied for semantic review or included in the public receipt.

Separate GPT-6.1 Sol review found **6/10 supported handoffs with thinking off**
and **3/10 with thinking on**. The off arm retained four decisive misses and three
unsupported critical claims. The on arm's three completed answers met the rubric;
its seven missing final answers each count as a decisive miss. No unsupported
claims were counted from those missing answers; that does not certify the unseen
partial content or reasoning. Previously supported repository-tour, concurrency
and injection handoffs were lost to truncation.

The reviewer received all twenty records with per-case mode labels shuffled,
exact source and existing keys, but no raw partial answers or reasoning traces.
Mode mapping was withheld by instruction and may be inferred from failures.
The root agent subsequently checked the final notes and judgments. This is
known-case AI review, not authenticated blindness or independent human
qualification. All final notes, failures and judgments are retained in the
[sanitized receipt](../examples/receipts/qwen3-8b-thinking-2026-11-05.json).

## Validation and decision

All 176 application tests passed, and eleven focused private probe checks passed.
The probe checks cover capture without chat transmission, replay without network
access, separation of diagnostic and production acceptance, and preservation of
truncation, tool, remote, model, reference, duplicate-key and usage refusals.
Live request equality and frozen runner/source identities were also verified.
No package, MCP adapter or installed application was modified.

All twenty responses arrived within the fixed deadline; no transport timeout or
identity change occurred. The seven incomplete responses all reported 512
generated tokens. Thinking-off responses reported 1,258 generated tokens in total;
thinking-on responses reported 4,916, including unfinished work. These are local
server counters, not cloud usage or token-savings evidence. Response elapsed-time
sums were 28.610113 and 53.525333 seconds respectively, with uncontrolled model
load/cache state and no peak-memory measurement; do not infer a general speed ratio.

The owned temporary loopback daemon started with cloud disabled, reused existing
weights and exited cleanly. Model manifest hashes and existing key-file metadata
were unchanged; the shared daemon was not reconfigured. This is configured local
execution, not a network-isolation attestation. The separately authorized Codex
AI review is a different activity.

The gate required all ten thinking responses to complete, at least seven supported
handoffs, no critical unsupported claims and no regression against the paired
thinking-off arm. Completion alone already fails. The settings therefore remain
unqualified. Any later output-budget experiment must declare its new cap before
generation, keep the deadline and source boundaries explicit, retain these failed
responses and use another reserved cohort only after development checks pass.

The [subsequent four-arm budget comparison](thinking-budget-2026-11-05.md) added fresh controls and explicitly declared 1,024/2,048-token thinking arms. Each larger budget completed nine answers but supported only six, retained two critical unsupported claims and lost concurrency to truncation. Both were rejected; this earlier 512-token record remains unchanged in scope.
