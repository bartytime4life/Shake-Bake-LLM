# Orientation brief on eight multi-file fixes: both rules met

Status: completed November 8, 2026, under a protocol pushed as `9e59236`
before any row at `dev` offsets 700 to 1199 was read
(`benchmarks/orientation-comparison-2026-11-08/protocol-multifile.json`). The
candidate is unchanged from the [first orientation run](orientation-comparison-2026-11-08.md):
`brief --style orientation`, frozen at `e537327` (`0.4.0.dev21`), with the
`briefing.py` and `search.py` hashes checked before any brief was rendered.
This run asked for a gain, not only the absence of harm, and both registered
rules were met. The gain is small, mostly on the paste path, and it comes with
more tokens, not fewer.

## Cases

Eight never-read Long Code Arena `dev` rows whose fixing pull request changed
at least two code files: readthedocs, cupy, docker-py, falcon, sqlfluff,
python-for-android, conan and dbt-core. There are 19 changed files in total, two
to four per case. Of the 500 rows read, 69 were excluded for a repository used
in an earlier run, 137 for not being multi-file, 7 by reserved `test` id and 72
for size. One case per repository was chosen by hash with no
replacements, and 88 MB was fetched with no omissions. The selection and
acquisition records are committed and no issue text is.

Hosts, prompts and arms are identical to the first orientation run: Claude
Code `general-purpose` subagents on the `sonnet` alias, one run per case and
arm. All 32 transcripts were audited for paths outside the run's own
directory and for git, network or package commands. There were no
violations. Six automatic flags turned out to be relative paths after `cd`,
`/dev/null` redirects and a `find` exclude pattern.

## Results

Changed files named in the top five, out of 19:

| Arm | Hits | Median tool calls | Median tokens | Median seconds |
| --- | ---: | ---: | ---: | ---: |
| Tools, no brief | 9 | 3.5 | 86,341 | 9.6 |
| Tools + orientation brief | **11** | 4 | 87,567 | 11.8 |
| No tools, issue only | 9 | 1 | 81,916 | 7.6 |
| No tools, issue + orientation brief | **13** | 2 | 83,978 | 7.3 |

- **Tools path:** 11 against 9, two wins and no losses, so the rule is met.
  Both wins are test files the fixing pull request also changed: docker-py's
  `tests/unit/models_images_test.py` and dbt-core's `test/unit/test_jinja.py`.
  Every source file found with the brief was also found without it. Median
  tokens rose by about 1,200, and the arm took one more tool call and two more
  seconds at the median.
- **Paste path:** 13 against 9, five wins and one loss, so the rule is met.
  The wins break down as follows:
  - **Source files the issue did not name:** readthedocs `projects/tasks.py`
    and python-for-android `ci/constants.py`.
  - **A test file:** cupy's `test_raw.py`.
  - **The repository's actual layout:** without the brief, the host guessed
    sqlfluff's later `core/linter/` package and dbt's pre-`core/` paths, and
    both were wrong at this commit.
  - **The loss:** falcon, where the issue-only host listed
    `tests/test_default_router.py` and the brief-reading host did not, even
    though the brief contained it.
- **Collector recall:** the briefs contained 15 of the 19 changed files. The
  four missing were three test files and one recipe file.

## Pooled over both orientation runs

The registered decision does not use these numbers. They cover fourteen fresh
cases and 29 changed files:

| Comparison | Brief hits | No-brief hits | Wins | Losses |
| --- | ---: | ---: | ---: | ---: |
| Tools path | 18 | 15 | 3 | 0 |
| Paste path | 19 | 15 | 5 | 1 |

Against the evidence brief's record on the earlier six cases, the change is
large. The evidence brief got 7 against 14 with tools and 9 against 10 pasted,
with four losses.

## What this establishes and what does not

- On this sample, a host given the orientation brief named more of the files
  a real fix changed, on both paths. That is the first measured gain for any
  brief in this project.
- The paste path is the workbench's main use, pasting into a chat with no
  repository, and the gain is clearest there. The brief supplies real paths
  and related files the host cannot otherwise see.
- On the tools path the gain is two test files. The host found the same
  source files either way.
- It does not establish token, tool-call or time savings. Every brief arm
  used more tokens at the median. It also says nothing about ChatGPT, other
  Claude models or other task types.
- The limits are eight cases, one run each, and a gold standard that counts
  test files. The hosts were not told whether to include tests. Public issues
  may be in the host's training data, and isolation was by instruction, then
  audited.

## What follows

The evidence now supports making the orientation framing the layout the
workbench copies. The evidence brief lost four of its twelve paired
comparisons. Across both orientation runs, the orientation brief lost one of
twenty-eight. The owner said to proceed, and the port shipped in `0.4.0.dev22`
([record](workbench-orientation-2026-11-08.md)). The brief should still not be
described as saving tokens, and any claim that it improves answers should be
limited to this measurement.

Run data is in `benchmarks/orientation-comparison-2026-11-08/`, in the files
`result-multifile.json`, `selection-record-multifile.json` and
`acquisition-multifile.json`. It includes usage, named files, hits, input
hashes and the isolation audit, but no issue text.
