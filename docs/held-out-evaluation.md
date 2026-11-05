# External evaluation datasets

The trial tools can now read an owner-selected dataset outside the checkout. This removes the hardcoded ten-case restriction; it does not establish that any supplied case is unseen or qualifies a model. The bundled Task Lab always remains development data, even when selected with `--dataset`.

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

Case IDs use lowercase letters, digits, underscores and hyphens, starting with a letter. Tasks and SearchLimits use the same core bounds as the application. External split choices are `development` or `held_out`; a held-out dataset inside the application's checkout is refused. The split is always recorded as an owner declaration, not an authenticated proof of independence.

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

Only the task and bounded source evidence go into preparation. Keys, dataset labels and review expectations are not sent to the model. Path traversal, duplicate cases, unsafe limits, symlinks, hard links and special fixture files are refused. Fixture hashing is bounded to 4,000 entries, 256 KiB per file and 32 MiB of file bytes. These are trusted local evaluation inputs, not a hostile-filesystem sandbox. The loader cannot detect an owner copying answers into a fixture or reusing previously exposed cases.

Run evidence-only first with an installed Python 3.11+ interpreter, using separate paths for input and output:

```bash
PYTHONPATH=src python3.14 -B benchmarks/model_trial.py run \
  --evidence-only --dataset /absolute/private-cases \
  --output /absolute/private-trials/evidence-v1 --seed 17
```

Then explicitly select an installed candidate for a separate run, if the source and daemon are permitted:

```bash
PYTHONPATH=src python3.14 -B benchmarks/model_trial.py run \
  --model exact-installed-model:tag --dataset /absolute/private-cases \
  --output /absolute/private-trials/candidate-v1 --seed 17
```

No daemon starts, download or cloud call is added. Output directories are created new and cannot enter the dataset or overwrite earlier runs. Receipts bind the manifest, keys, source fixtures, preparation pipeline, runtime and requested settings. Every finished attempt is checkpointed; input drift stops the trial, including grading changes during the final attempt. Accuracy remains unset until the separate receipt-bound review is completed. Interrupted attempts do not create a complete score.

Use `model_trial.py score --trial /absolute/run/trial.json --reviews /absolute/run/reviews.json` after reviewing every attempt against exact evidence. Failures remain in the denominator. Repeated cases are not independent examples. These receipts can contain source and model outputs; keep them private.

## The next experiment still required

Reserve clean, defective, no-answer, cross-file and misleading-comment cases that were not used to tune the candidate. Record expected findings and prohibited claims before opening model results. Compare the same native host/settings and source across native retrieval, deterministic helper evidence, and helper evidence plus candidate notes. Judge the **final task outcome**, critical misses, unsupported claims and useful abstention; include retries, follow-up evidence, failures, correction time and actual usage when available.

The new runner captures local preparation and separate human handoff review. It does not run or score actual Claude/ChatGPT final answers, prove dataset blindness, perform a paired host study, calculate cloud savings or promote routing profiles. Full device/runtime/settings qualification remains separate. No real held-out study was performed to verify this implementation; tests use temporary synthetic data and a simulated model service.
