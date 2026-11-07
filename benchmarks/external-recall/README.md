# External file-recall cases

`benchmarks/external_recall.py` measures the unchanged collector on
localization cases this project did not author: given a request and the files
a real fix changed, how many of those files appear among the exact excerpts
(primary, then with controlling context) and the path map. It is mechanical
recall at a declared byte and file budget. It is not answer accuracy, it runs
no model and no cloud host, and public datasets may be inside a cloud model's
training data, so a number here qualifies the collector only.

## Case file

A JSON Lines file, one case per line:

```json
{"id": "repo#123", "root": "repo-at-base-commit", "request": "issue title and body", "changed_files": ["src/a.py", "tests/test_a.py"]}
```

`root` is a directory holding the repository checkout at the commit before the
fix, relative to `--repos` or absolute. It must be outside this checkout.
`changed_files` are repository-relative POSIX paths. Keep case files, receipts
and repositories outside the checkout; nothing here is committed.

```bash
python3.12 -B benchmarks/external_recall.py --cases /abs/cases.jsonl --repos /abs/repos --max-files 1000 --seconds 30 --output /abs/receipt.json
```

Add `--rerank-model <installed embedding model>` to reorder the top lexical
candidates with a loopback Ollama embedding model before selection; the
receipt then records the rerank outcome per case. Nothing is downloaded.

The default collector limits (200 files, 5 seconds) are the application's
defaults and will hit `file_budget` on most real repositories; the receipt
counts how many cases did. Raising the limits up to the ceilings in
`SearchLimits.validate` shows what the collector can reach when allowed, which
is a different number from what the shipped defaults reach.

## Building cases from Long Code Arena bug localization

The JetBrains Research dataset `lca-bug-localization` (Hugging Face) pairs
GitHub issues with the pull requests that fixed them, in Python, Java and
Kotlin, with `dev`, `train` and `test` splits; repositories are fetched
separately from its `repos.json`. Before any download, check the dataset's
license and the licenses of the repositories it points at, and record the
dataset revision in the receipt's notes. Use the request text exactly as the
issue gives it; do not rewrite it. Use only the `test` split for a held-out
number and keep it unread until the collector change under test is frozen.

Each case maps to: `id` = repository and issue number, `root` = the checkout at
the base commit, `request` = issue title and body, `changed_files` = the files
the fixing pull request modified.

## Reading the receipt

- `mean_recall_primary`: changed files among the actual primary excerpts (at most four windows).
  The collector's controlling-context E-ids distinguish added context from primary
  windows even when fewer than four primary windows were selected.
- `primary_excerpts` and `controlling_context_excerpts`: per-case window counts,
  reported separately from file-level recall; multiple windows may share a file.
- `mean_recall_excerpted`: changed files among all excerpts, including
  controlling context.
- `mean_recall_with_map`: changed files among excerpts plus the path map.
- `cases_with_any_*`: fraction of cases where at least one changed file was
  reached at that level.
- `cases_hitting_file_budget` and `cases_hitting_time_budget`: how often the
  walk stopped early; a low recall with a high budget count is a limit, not a
  ranking result.

Compare two collector versions on the same case file and limits; do not tune on
the `test` split and then report it as held out.
