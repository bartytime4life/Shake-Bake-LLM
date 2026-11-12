# External evaluation datasets

Guidance refreshed November 11, 2026. [Current build status](current-status.md)
identifies the reviewed dev37 code and its mechanical verification;
[evaluation status](evaluation-status.md) records development and previously
reserved cohorts separately. A larger output budget, newer UI or green test
suite does not create unseen evidence. Freeze and pass the candidate
development gate before using a new reserved cohort.

The trial tools accept an owner-selected dataset outside the checkout. This
removes the bundled ten-case restriction; it does not establish that a supplied
case is unseen or qualifies a model. The bundled Task Lab remains development
data even when selected with `--dataset`. This manifest/fixture format is
separate from the JSON Lines case format for [external file
recall](../benchmarks/external-recall/README.md).

Keep private cases out of Git and freeze them before tuning. Use a quiescent directory with this layout:

```text
private-cases/
  manifest.json
  grading-keys.json
  fixtures/
    case-one/
      source.py
```

The manifest has this structure. The values below illustrate the format; they are not a qualification dataset:

```json
{
  "schema_version": "1",
  "dataset_id": "owner-reserved-cohort-v1",
  "split": "held_out",
  "cases": [
    {"id": "case-one", "task": "Explain the source boundary and its missing evidence.", "limits": {}}
  ]
}
```

The manifest permits 1–1,000 cases. Case IDs are 1–64 lowercase letters, digits,
underscores or hyphens, starting with a letter; tasks are nonempty and at most
16,384 characters, subject to the application's valid-text checks. Each
`limits` object accepts only `SearchLimits` fields and validates their values.
An empty object uses the current defaults: 1,000 files, 20,000 entries, depth 8,
five walk seconds, 16,384 excerpt bytes and 2,048 context bytes. The [file-recall
guide](../benchmarks/external-recall/README.md) lists all six supported ranges.
Context bytes are within the shared excerpt budget. Up to four primary and
six controlling-context windows may be selected, subject to those caps; case
limits do not make lexical selection exhaustive.

External split choices are `development` or `held_out`; a held-out dataset
inside the measurement checkout is refused. The split is always recorded as
an owner declaration, not an authenticated proof of independence. Freeze case
exposure history as well as bytes: rereading an exposed case cannot restore
its unseen status.

Keep the grading document outside every fixture root:

```json
{
  "schema_version": "1",
  "never_send_to_worker": true,
  "cases": {
    "case-one": {
      "anchors": [{"path": "source.py", "contains": "expected exact source span"}],
      "required_cutoffs": [],
      "required_findings": ["Human review expectations belong here, outside model inputs."]
    }
  }
}
```

Each case permits up to 32 anchors and 16 required-cutoff labels. An anchor is
an exact `(path, contains)` pair; `contains` is 1–4,096 characters and must fit
within one excerpt for a mechanical hit. Required-cutoff labels are at most 64
characters each. Case IDs in the keys must match the manifest exactly.

Only the task, bounded source evidence and software-produced collection facts
go into preparation. Keys, dataset labels and review expectations are not sent
to the model. Path traversal, duplicate cases, unsafe limits, symlinks, hard
links and special fixture files are refused. Manifest/key reads are capped
at 256 KiB each. Fixture hashing is bounded to 4,000 entries, 256 KiB per file
and 32 MiB of file bytes per case. These are trusted local evaluation inputs,
not a hostile-filesystem sandbox. The loader cannot detect an owner copying
answers into a fixture or reusing previously exposed cases.

Run from the trusted project root with Python 3.11 or newer, substituting an
explicit supported interpreter if the default `python3` is older. Use separate
paths for input and output and run evidence-only first:

```bash
PYTHONPATH=src python3 -B benchmarks/model_trial.py run \
  --evidence-only --dataset /absolute/private-cases \
  --output /absolute/private-trials/evidence-v1 --seed 17
```

Then explicitly select an installed candidate for a separate run, if the source and daemon are permitted:

```bash
PYTHONPATH=src python3 -B benchmarks/model_trial.py run \
  --model YOUR_INSTALLED_MODEL --dataset /absolute/private-cases \
  --output /absolute/private-trials/candidate-v1 --seed 17
```

Replace `YOUR_INSTALLED_MODEL` with the exact permitted installed name. This
second command explicitly requests local inference. It starts no daemon,
downloads no model and invokes no cloud host. The shipped worker requests
`handoff_prompt_v1`, 8,192 context tokens, 1,024 output tokens, thinking off and
a shared 30-second deadline; those are requested settings, not runtime
attestation or a tuned/qualified profile. The runner accepts `--repeat` 1–3
and repeatable `--case` IDs. It exposes no generation-budget override.

Output directories are created new and cannot enter the dataset or overwrite
earlier runs. Receipts bind the manifest, keys, source fixtures, preparation
pipeline, runtime and requested settings. Every finished attempt is
checkpointed; input drift stops the trial, including grading changes during
the final attempt. Accuracy remains unset until the separate receipt-bound
review is completed. Interrupted attempts do not create a complete score.

After reviewing every attempt against exact evidence, score the matching run:

```bash
PYTHONPATH=src python3 -B benchmarks/model_trial.py score \
  --trial /absolute/private-trials/candidate-v1/trial.json \
  --reviews /absolute/private-trials/candidate-v1/reviews.json
```

Failures remain in the denominator. Repeated cases are not independent
examples. These receipts can contain source and model outputs; keep them private.

## Recorded exposure is dated

The [November 8 frozen collector comparison](frozen-recall-2026-11-08.md)
selected twelve previously unread LCA Python cases only after freezing its
protocol and excluding prior exposure, including rows overlapping `dev` and
`test`. Those twelve are now exposed. Thirteen other rows remained reserved
in that record; that is not a current audit of other runs or agents.

The [November 11 source-span diagnostic](source-span-development-2026-11-11.md)
uses six authored development cases tailored to known selection changes. Its
pinned comparison retains the oversized-anchor miss and supplies no new
reserved cohort. The [receipt-limit compatibility
replay](recall-comparison-limits-2026-11-11.md) only recomputes retained public
receipt pairs. Neither result resets exposure or qualifies a model/host.

## The next experiment still required

Reserve clean, defective, no-answer, cross-file and misleading-comment cases that were not used to tune the candidate. Record expected findings and prohibited claims before opening model results. Compare the same native host/settings and source across native retrieval, deterministic helper evidence, and helper evidence plus candidate notes. Judge the **final task outcome**, critical misses, unsupported claims and useful abstention; include retries, follow-up evidence, failures, correction time and actual usage when available.

The runner captures local preparation and separate handoff review; label whether the reviewer is a human or an AI. It does not run or score actual Claude/ChatGPT final answers, prove dataset blindness, perform a paired host study, calculate cloud savings or promote routing profiles. Full device/runtime/settings qualification remains separate. Implementation tests use temporary synthetic data and a simulated model service. A subsequent [owner-PC frozen-prompt comparison](reasoning-screening-2026-11-05.md) used ten newly authored synthetic cases outside tuning and separate masked AI review: 2/10 original and 3/10 experimental handoffs met the rubric. The prompt experiment was rejected. This is a completed local preparation comparison, not independent human qualification or a paired native-host final-task study. Its now-exposed cohort must not be relabeled unseen after future tuning.
