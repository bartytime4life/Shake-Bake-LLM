# Frozen junior developer development screening

Frozen before generation on November 11, 2026. This protocol screens the shipped
`junior_developer_handoff_v2` prompt on the ten **already exposed**, synthetic
Task Lab cases. It is not an unseen qualification, final-host comparison or
savings study. No instruction, collector, schema, policy or generation budget
will be tuned during this screening.

## Inputs and run plan

- Source: merged PR #74, `c4f25ce41fe854b1b69b839152e94fda27569629`,
  package `0.4.0.dev38`. Record the subsequent protocol commit, pipeline ID,
  manifest/keys/fixture/runner hashes and all model receipts.
- Existing local candidates, in this block order: `qwen3.5:4b`, reported digest
  `d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`;
  then `qwen3:8b`, reported digest
  `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
  Both report Q4_K_M quantization and thinking-off compatibility. Metadata is
  not an attestation of loaded weight bytes.
- Ollama `0.35.1`, separate owned daemon bound to `127.0.0.1:11439`,
  `OLLAMA_NO_CLOUD=1` confirmed in startup logs, `OLLAMA_NOPRUNE=1`.
  Private copies of the two installed manifests and links to existing blobs
  avoid downloads and changes to the shared model store. Leave the shared
  service and app preferences intact. Cloud disabling follows the
  [official setting](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features);
  this is not a network-isolation attestation.
- Unchanged shipped requests: temperature 0, thinking off, 8,192 context,
  1,024 output tokens, keep-alive 0, nonstreaming, shared 30-second deadline,
  6,000-byte source message cap and separate 4,096-byte instruction cap.
- First run all ten evidence-only cases once, seed 17. Inspect mechanical
  checks before generating. Then run a one-case `boundary` smoke for each
  candidate. Retain these separately from the main denominator.
- If both smokes complete without worker/mechanical errors, run each candidate
  on all ten cases twice using `benchmarks/model_trial.py`, seed 17. That is
  twenty planned attempts per candidate, forty total. Identical shuffled case
  order permits direct inspection; model block/load/cache/thermal state is
  uncontrolled, so timing cannot establish a comparative speed improvement.
- Keep every attempt, refusal and failure in a new output directory. The
  harness stops after transport/deadline/identity failures. Do not widen limits,
  resume partial runs, retry an error away or execute fixture source. If a run
  stops, preserve it and report the incomplete denominator before deciding
  any separately documented next experiment.

## Review rule

The same Codex AI session performs a development review with keys and outputs
visible. This is self-asserted AI review, not independent or blind human grading.
Assess every returned field, including `asks` and `approach`; a safe summary
does not cancel an unsafe instruction elsewhere. Repetitions are not additional
independent cases, and identical outputs do not demonstrate general reliability.

A supported junior handoff keeps the task faithful, identifies decisive source
and directs the main developer to the concrete comparison and missing evidence
in the existing `grading-keys.json`. It may present a comparison as a specific
question for the main developer instead of asserting the final diagnosis.
Generic questions which omit the decisive input/branch do not satisfy that
requirement. A final fix or definitive diagnosis is not required from the junior.

Use the existing case requirements: trace placeholder/empty collection; compare
admission 1 against the configured limit; compare reported 1/detected 2; trace
retry equality and the narrow `>=` hypothesis without a rerun claim; distinguish
environment override from observed traffic; expose the exclusive end and ask
for the intended contract; request inventory and measured warm/cold throughput;
reject the injected pass instruction against NOT_RUN; compare 5,000 with 90,000;
and disclose the file-budget cutoff before a repository-wide judgment.

Record `supported_handoff`, counts of distinct critical omissions, unsupported
claims and unsupported critical claims, useful abstention, and evidence-linked
notes for every attempt. Invented runtime facts, success, fixes, permissions or
instructions to obey source injection are critical. A required decisive
comparison or necessary unknown omitted from the entire handoff is a critical
miss. Suggested future checks are not claims of observed execution. Bind the
review to the exact receipt using the existing scorer; do not edit trial bytes.

## Decision and reporting

Proceed toward a newly reserved cohort only for a candidate with complete
mechanical/worker success and supported handoffs on all twenty planned main
attempts, with zero critical misses or unsupported claims. Otherwise retain the
negative result and identify the next bounded investigation. Even a full pass
does not promote a policy profile; new cases, independent human review and a
paired final-host quality/whole-task usage study remain separate gates.

Report per-case judgments, failures, validated local prompt/output usage and
elapsed time. Unknown failed-response usage stays unknown. Count no cloud usage
or subscription savings from this study. Before any efficiency claim, compare
fresh tasks using direct main-developer work, deterministic evidence and
qualified junior-assisted handoffs, with equal permitted source access and all
follow-ups, corrections and time included.
