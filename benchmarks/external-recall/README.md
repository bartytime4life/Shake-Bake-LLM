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
`changed_files` are repository-relative POSIX paths. Keep case files, live receipt outputs
and repositories outside the checkout. The reviewed public audit exports
linked below contain only hashes, counts and public localization metadata,
not issue bodies, source packets or local configuration.

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

The bundled repository archives are large (11 GB for the Python config), so
the November 7 run fetched each case's base commit directly instead:

```bash
git init repos/<owner>__<name> && cd repos/<owner>__<name>
git remote add origin https://github.com/<owner>/<name>.git
git fetch --depth 1 origin <base_sha> && git checkout FETCH_HEAD
```

That run's selection rule, manifest and receipts are under
`examples/receipts/external-recall-2026-11-07/`; the `dev` split it used is
development material and those cases are now exposed. The `test` split
(0.18 MB) stays unread until the collector change under test is frozen.

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

## Reproducible receipt comparison

New CLI receipts use schema 2. They record the exact case-file hash read during
parsing, a separate hash for the selected IDs/requests/gold paths, a hash of the
resolved case-root locations, on-disk collector and adapter source hashes, all
six collection limits, and Python/platform details. Persistent case-file or
code drift during collection refuses the run before writing a receipt. Existing
receipts are never overwritten; outputs inside the adapter checkout, imported
collector checkout or inspected case roots are refused. Duplicate case IDs and
nonpositive `--limit` values are refused.

These are provenance observations, not loaded-code attestation. Root-location
hashes do not establish that a corpus is unchanged: separately freeze and hash
the approved source snapshots before and after a run. Record dataset revision,
license checks, exclusions and acquisition omissions outside inspected roots.
Do not describe an owner-declared split or hash as independently verified.

Use one copy of this measurement adapter against both trusted, pinned collector
checkouts. It supports the three-argument lexical `prepare` interface from before
PR #30 and treats missing later rerank/line-index fields as absent. No model is
run unless the operator explicitly supplies `--rerank-model`.

For example, after preparing approved case roots outside all three checkouts:

```bash
measurement=/abs/current-measurement-checkout
before=/abs/trusted-dev10-checkout
after=/abs/trusted-pr30-checkout
cases=/abs/evaluation/cases.jsonl
repos=/abs/evaluation/repos
receipts=/abs/evaluation/receipts

PYTHONPATH="$before/src" python3.12 -B "$measurement/benchmarks/external_recall.py" --cases "$cases" --repos "$repos" --max-files 200 --max-entries 4000 --max-depth 8 --seconds 5 --excerpt-bytes 16384 --context-bytes 2048 --output "$receipts/before-default.json"
PYTHONPATH="$after/src" python3.12 -B "$measurement/benchmarks/external_recall.py" --cases "$cases" --repos "$repos" --max-files 200 --max-entries 4000 --max-depth 8 --seconds 5 --excerpt-bytes 16384 --context-bytes 2048 --output "$receipts/after-default.json"
python3.12 -B "$measurement/benchmarks/compare_recall_receipts.py" --before "$receipts/before-default.json" --after "$receipts/after-default.json" --output "$receipts/paired-default.json"
```

Create the receipts directory outside the case roots first. Pin the before
checkout to `2a0acdf4a4e3e70ee2dd1ab116826fdc04506295` and PR #30 to
`2222a67d4289a18abfb2305b9a62f5c9ab36c547`. Pin the measurement checkout too;
use the same adapter file for both runs. The historical pilot's expanded profile
uses `--max-files 1000 --max-entries 10000 --max-depth 16 --seconds 30`, keeping
the same excerpt/context bytes; collect and compare that profile separately.
The comparer refuses different file bytes, selected cases, root locations,
budgets, rerank configuration, Python/platform identities or adapter hashes, and refuses legacy receipts
without source/selection provenance. It does not compare helper-version strings
as proof of the scoring implementation.

The strict comparer is lexical-only. It refuses rerank receipts even when their
model tags match: a mutable tag does not establish identical weights/runtime.
That comparison needs a separate frozen model/runtime protocol. Python/platform
and declared timing scope must also match; matching strings do not attest to
identical hardware or cache state.

Results are recomputed from per-case hit counts on the common scored pairs.
One-sided refusals remain explicit and are omitted from both paired means.
Both per-case mean recall and total hits/micro recall are reported, with
wins/ties/losses, cutoffs, aggregate exclusions and single-call processing times.
Mean gains can coexist with case regressions or unchanged total file hits.
The comparer reads at most 16 MiB per input receipt and never overwrites output.

This recipe does not download datasets, install the application, promote a
model, establish corpus immutability or measure cloud-answer quality/costs.
The seven-case pilot remains historical evidence; these checks do not create a
new held-out performance result. See `pilot-protocol-2026-11-07.json` for the
pinned public dataset/protocol metadata; case text and source snapshots are not
committed here. The LCA `dev` split contains `test`, so those splits must not be
treated as disjoint development and held-out sets.


## Recorded independent audit

The [November 7 independent audit](../../docs/independent-retrieval-2026-11-07.md)
records nine of the original twelve selected Long Code Arena Python cases,
with paired mean/total recall, regressions, truncation, relevant-file exclusions
and timing. The original seven-case protocol above remains historical.
[The manifest and reviewed receipt exports](independent-2026-11-07/manifest.json)
pin the exact inputs and acquisition omissions. The native schema-2 receipts
are accounting replays on those already-exposed cases, not new held-out
results. The derived custom audit is explicitly labeled separately from them.

No issue bodies, source excerpts, full dataset, corpus snapshots or private
local configuration are committed. Attribution and third-party terms are in
[NOTICE](independent-2026-11-07/NOTICE.txt). New large downloads and installed
application changes still require a separately shown operation and approval.
