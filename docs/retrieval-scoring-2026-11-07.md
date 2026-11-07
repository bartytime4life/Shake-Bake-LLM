# Retrieval scoring and external file recall

Status: development changes in `0.4.0.dev11`, November 7, 2026. These are the
first three candidates from the [November 6 web research](research-2026-11-06.md),
the ones that need no model: BM25-style file scoring, a disclosed distractor
exclusion, and an adapter that measures the collector's file-level recall on
localization cases this project did not author. No model and no cloud host
were run. Primary selection still takes four windows; the controlling-context
pass is unchanged.

## What changed

**Scoring.** The walk now records, per matching file, which request terms each
line hits and which terms the path contains, and counts how many examined
files contain each term. After the walk, each matching file is scored
BM25-style: a term's weight is `log(1 + (N - df + 0.5) / (df + 0.5))` over the
`N` examined text files, repeated hits in a file saturate with `k1 = 1.2`, and
a path hit counts twice. Length normalization is off (`b = 0`): the seven-line
window is the retrieval unit, and the first attempt with `b = 0.75` ranked
one-line comment files above the real five-line match, which is the classic
short-document bias and wrong here. Inside a file, windows are placed on the
lines whose matched terms weigh most. Ties break by path, so results stay
deterministic.

**Distractor exclusion.** When at least eight text files were examined, a
matching file whose only hits are widespread terms (present in eight or more
examined files) and whose score is under a fifth of the best file is left out
of selection and the map, and counted in the receipt's exclusions as
`low_signal_match`. `matching_files` still counts it, so the receipt shows both
what matched and what was set aside.

**External recall adapter.** `benchmarks/external_recall.py` reads JSON Lines
cases (`id`, `root`, `request`, `changed_files`), runs the unchanged collector
at declared limits, and reports per case and in aggregate how many changed
files appear among the four primary excerpts, all excerpts, and excerpts plus
the path map, with cutoffs, exclusions and timing. Case roots must be outside
the checkout. [Its README](../benchmarks/external-recall/README.md) says how to
build cases from the Long Code Arena bug-localization dataset after a license
check; nothing was downloaded for this record.

## Measurements

**Task Lab.** All ten exposed evidence-only cases keep their required spans
(10/10 mechanical passes), as before.

**Four comparison fixtures** (generated outside the checkout from
`benchmarks/native-preparation`; decisive files from the grading keys):

| Case | Before (`dev10`) | After (`dev11`) |
| --- | --- | --- |
| dispatch-path | 7 excerpts, 6/6 decisive, 3,396 B | 7 excerpts, 6/6, 3,469 B |
| publish-reorder | 7, 6/7 plus 1 mapped, 3,697 B | 7, 6/7 plus 1 mapped, 3,697 B |
| two-log-failures | 7, 6/6, 5,099 B, map of 12 utility files, one utility file excerpted | 6, 6/6, 3,162 B, map empty, 18 utility files excluded as `low_signal_match`, both test files excerpted |
| deployment-unknowns | 5, 5/6 plus 1 mapped, 2,861 B | 5, 5/6 plus 1 mapped, 2,861 B |

The log case is the one the November 6 analysis called out: the request's
broad terms (`log`, `test`) had let a utility file into the primary four and
twelve more into the map. With document frequencies known, `log` (in 20 of 78
files) weighs 1.35 against 5.06 for terms found in one file, so
`tests/test_retry.py` replaces the utility file, and the exclusion removes the
rest. The other three cases are unchanged or within one line.

**Self-commit smoke, development material only.** Twelve recent non-merge
commits of this repository (228 tracked files) were exported at their parent
commit into a scratch directory, with each commit's subject and body as the
request and its changed files as the target. These commits were written by the
same AI sessions that wrote the collector, touch 2 to 27 files each, and are
mostly documentation; the numbers show the adapter working on a real-sized
tree and the direction of the scoring change, nothing more.

| Measure (12 cases) | `dev10` scoring | `dev11` scoring |
| --- | ---: | ---: |
| Mean recall, four primary excerpts | 7.4% | 12.9% |
| Mean recall, all excerpts | 10.7% | 18.6% |
| Mean recall, excerpts plus map | 26.2% | 38.3% |
| Cases with any changed file in the primary four | 6/12 | 9/12 |
| Cases with any changed file in excerpts | 9/12 | 9/12 |
| Cases with any changed file reached including the map | 11/12 | 12/12 |
| Cases hitting the file or time budget | 0 | 0 |

Per-case hits moved up in ten cases, stayed equal in one and lost one primary
hit in one (3 to 2, with the same three files still excerpted). Each run took
45 to 76 milliseconds per case. Both receipts are retained under
`examples/receipts/retrieval-scoring-2026-11-07/`; raising the walk limits to
their ceilings changed nothing because this tree is under the default budget.

## Program checks

195 Python tests pass under Python 3.12, six new: rare terms outrank
widespread ones with the exclusion counted; the exclusion needs enough files
and only widespread hits; deterministic order with no short-file advantage;
recall levels, refusals and receipt fields; the CLI writing a receipt outside
the checkout with a file-budget cutoff; roots inside the checkout and invalid
rows refused. Node checks are unaffected (no workbench change).

## What this does not establish

- Recall on cases authored by other people. The adapter exists; the external
  run needs the owner's license check and download, and the `test` split must
  stay unread until the collector change under test is frozen.
- Fewer host turns or any accuracy result; no host or model ran.
- That the exclusion never removes a relevant file. It removes only files whose
  every hit is a widespread term and whose score is a fifth of the best; the
  receipt discloses the count so a reviewer can look.
- Behavior on repositories above the default walk budget, where `file_budget`
  truncates the walk before scoring; the adapter counts those cases so the
  limit is visible in any external run.
