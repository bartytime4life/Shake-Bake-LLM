# Larger thinking budgets — November 5, 2026

Neither larger thinking budget passed the frozen development gate. At both
1,024 and 2,048 tokens, Qwen 3 8B completed nine final answers and produced six
supported handoffs out of ten. The concurrency case remained truncated, and two
critical unsupported claims remained. Thinking off also produced six supported
handoffs. The application and its acceptance rules remain unchanged.

This follows the [512-token thinking probe](thinking-probe-2026-11-05.md).
The new run included fresh controls, rather than treating the earlier run as a
contemporaneous comparison. All forty attempts, validated final notes and review
decisions are retained in the [synthetic receipt](../examples/receipts/qwen3-8b-budget-2026-11-05.json).

## Frozen comparison

The same ten bundled, exposed development cases ran once in each of four arms:
thinking off at 512 tokens, and thinking on at 512, 1,024 and 2,048 tokens. Seed 17
shuffled cases; arm order rotated cyclically by case. No generation seed was
supplied. This is a small development experiment, not a population accuracy estimate.

Before generation, the private runner captured the exact production requests and
verified their equality with the earlier frozen source, prompt and schema. Only
`think` and `options.num_predict` could differ across arms. Temperature 0, the
8,192-token context request, `keep_alive=0`, non-streaming transport, 6,000-byte
message cap, 262,144-byte response cap and shared 30-second deadline were retained.
The declared caps were never increased during the run, and no attempt was retried.
Grading keys stayed outside fixture roots and were not sent to Ollama.

The reported model was `qwen3:8b`, Q4_K_M, digest
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`,
with Ollama `0.35.1`. The unchanged production pipeline was
`3beaa7d1618112b9f5b5c76f4aac07eec897ab3b7b6d9a545d3c5c70ae663b09`.
The receipt separately pins the plan, private runner, worker bytes and dataset.
These are requested settings and reported identities, not weight-byte attestation.

## Completion and correctness

| Arm | Complete final JSON | Supported handoffs | Decisive misses | Critical unsupported claims | Truncated | Accepted by production-validator replay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Thinking off, 512 | 10/10 | 6/10 | 4 | 3 | 0 | 10/10 |
| Thinking on, 512 | 3/10 | 3/10 | 7 | 0 | 7 | 0/10 |
| Thinking on, 1,024 | 9/10 | 6/10 | 4 | 2 | 1 | 0/10 |
| Thinking on, 2,048 | 9/10 | 6/10 | 4 | 2 | 1 | 0/10 |

Every missing final answer remains in the ten-case denominator with one decisive
miss. Zero counted unsupported claims for a missing answer does not certify its
partial content or reasoning. Structural acceptance is separate from correctness.

The nine completed larger-budget answers had identical summaries, evidence IDs
and questions across 1,024 and 2,048 tokens. Their material findings were:

| Case | Result at both larger budgets |
| --- | --- |
| Failed-test triage | Improved: explains the equality failure and explicitly proposes `>=` as an untested correction hypothesis. It does not claim an applied change or successful rerun. |
| Concurrency | Regressed from thinking off: no final content, with `done_reason=length` at each requested cap, including 2,048 tokens. |
| Change review | Still incomplete: correctly identifies scalar `detected`, but omits the requested before-allows/after-rejects example, such as reported length 1 with detected 2. Ambiguous wording about narrowing the condition was retained as an explanation issue, not counted as a proven false assertion. |
| Unknown hardware | Still unsupported: treats an example candidate as known to be absent, although no installed-model inventory was supplied. |
| Runtime mode | Still unsupported: calls the remote branch unspecified even though the source supplies its endpoint return. Actual environment and traffic remain unknown. |

Repository-tour, boundary, coverage-budget, distant-contradiction and injection
also met the disclosed central-finding rubric. Redundant questions, ambiguous
wording and missing explanatory detail remain visible in the receipt. These
passes do not mean every sentence is ideal or every intended-contract question
has been settled.

## Review and acceptance boundaries

GPT-6.1 Sol reviewed all forty records against exact source and the existing keys.
Per-case labels were shuffled; settings, usage, mapping, raw partial answers and
reasoning were omitted from its packet. Identical final notes received identical
judgments. The root agent then checked the final notes and judgments. Masking was
by instruction and could be inferred; the reviewer had prior exposure to these
known cases. This is separate AI grading, not authenticated blindness, independent
human qualification or held-out accuracy.

The production worker still requests thinking off and rejects returned thinking.
The private diagnostic replayed an unchanged response through that validator,
then separately replayed a copy with only `message.thinking` omitted to assess
final content. That projection preserved truncation, malformed JSON, unknown
references, tool, remote/model and usage refusals. It is not production acceptance
or a new supported configuration. Raw bounded responses remain private; public
receipts include only validated final notes and failure metadata.

## Validation, cost observations and decision

Fourteen focused private probe checks passed before generation, including nested
request/source preservation, refusal of undeclared arms, offline validation and
separation of diagnostic acceptance from production acceptance. Frozen runner,
dataset and request identities were checked. The application source, installed
wheel and MCP adapter were not changed; the existing application baseline has 176
passing tests. Hosted source, installed-package and browser checks are recorded
separately on the report PR.

| Arm | Reported generated tokens, including failures | Sum of response elapsed time | Longest response |
| --- | ---: | ---: | ---: |
| Thinking off, 512 | 1,258 | 28.570359 s | 3.177951 s |
| Thinking on, 512 | 4,916 | 53.429171 s | 5.526340 s |
| Thinking on, 1,024 | 6,267 | 62.522923 s | 8.987048 s |
| Thinking on, 2,048 | 7,291 | 69.806453 s | 16.093498 s |

All forty transport responses arrived within the deadline. The 2,048-token arm
reported 1,024 more generated tokens than the 1,024-token arm, entirely in the
still-incomplete concurrency response. These are local server counters and one
run's timing; cache/load state was uncontrolled, peak memory was not measured,
and no cloud savings or general speed ratio follows.

The owned temporary daemon confirmed cloud-disabled configuration, reused existing
weights and exited cleanly. Manifest hashes and existing key-file metadata stayed
unchanged. The shared daemon was preserved. This is configured local execution,
not network-isolation attestation; the authorized Codex AI review is separate.

The gate required ten complete thinking responses, at least seven supported
handoffs, zero critical unsupported claims and preservation of all contemporaneous
and previously supported baseline cases. Both larger budgets fail every one of
those conditions. No finalist was selected and no new reserved cohort was started.
Keep these failures and test a separately frozen candidate or task design on
development material before spending a new cohort. A paired final-host study and
human qualification remain distinct gates; see [current evaluation status](evaluation-status.md).
