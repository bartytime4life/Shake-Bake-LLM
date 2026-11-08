# Paste-path comparison: the brief did not help a host without tools either

Status: completed November 8, 2026, under a protocol pushed as `7208c45`
before any run. It follows the [host comparison](host-comparison-2026-11-08.md),
whose record named the paste-into-chat path as the most likely place the brief
still matters: there the host cannot explore, and the brief is all it has
beyond the issue. On this sample it did not help. The pre-registered rule is
not met.

## Setup

Same six Long Code Arena cases, same issue and brief files (hashes in the host
comparison's `inputs-sha256.json`), same host type and model, one run per case
and arm. Each host's directory held only the pasted text, with no repository:
`issue.md` alone, or `issue.md` and `brief.md`. The task and answer format were
the same as before: name up to five files that must change.

## Results

| Case | Gold files | Issue only: hits | Issue + brief: hits |
| --- | ---: | ---: | ---: |
| pysyft | 4 | 2 | 2 |
| openbbterminal | 2 | 2 | 1 |
| sanic | 3 | 3 | 3 |
| netbox | 9 | 1 | 1 |
| pip | 3 | 1 | 1 |
| dvc | 4 | 1 | 1 |
| **Total** | **25** | **10** | **9** |

The brief won no case and lost one; median host tokens were 87,046 with it
against 81,417 without. **Registered decision: not met.**

The one loss is the same failure the host comparison showed. In
openbbterminal the brief's second excerpt is a near-copy of the failing
function in another module, `comparison_analysis/market_watch_view.py`, and
the host named it in place of the real second file,
`fundamental_analysis/market_watch_view.py`, which it had named from the issue
alone. In dvc the host itself called the brief's excerpts "mostly noise from
lexical matching".

## The four arms side by side

| Arm | Changed files named, of 25 |
| --- | ---: |
| Tools, no brief | 14 |
| No tools, issue only | 10 |
| No tools, issue + brief | 9 |
| Tools + brief | 7 |

Two readings follow, both bounded by six cases and one run each.

- **A capable host is a better localizer than the collector.** With tools it
  found twice the files the brief-anchored host did, in four calls on median.
- **The brief anchors.** In both paths the host treated the excerpts as the
  answer's boundary; when an excerpt was a look-alike, it misled. The issue-only
  figure is probably inflated by the host's prior knowledge of these public
  projects, which would make the brief's net effect, if anything, worse than
  shown.

## What this does not establish

- That a differently framed brief would fare the same; the framing was not
  varied here.
- Anything about tasks other than naming files to change, other hosts
  (ChatGPT, other Claude models), private repositories the host cannot know,
  or repeat-to-repeat variance.
- Answer correctness beyond file names.

Run data (usage, named files, hits; no issue text) is under
`benchmarks/paste-comparison-2026-11-08/`.
