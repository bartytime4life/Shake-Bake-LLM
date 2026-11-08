# Frozen `dev20` collector on reserved Long Code Arena cases

Status: completed November 8, 2026. A pre-registered, frozen comparison of
the `0.4.0.dev20` collector against the PR #30 collector on twelve Python
`test`-split cases that no earlier Shake & Bake run had read. The registered
decision rule is met. This measures file recall of the collector only: no
model, no host, no answer quality, no tokens or cost.

## What was fixed in advance

The [protocol](../benchmarks/external-recall/frozen-dev20-2026-11-08/protocol.json)
was committed and pushed as `559d361` before any reserved row was read. It
fixes:

- **Pool.** The 50 Python `test` rows, minus the 12 used by the
  [November 7 independent audit](independent-retrieval-2026-11-07.md), minus
  any row among the 300 `dev` rows read on November 7 (the `dev` split
  contains `test`).
- **Selection.** The first 12 ids of the pool by `sha256(seed + text_id)` with
  the seed `shake-bake-frozen-dev20-2026-11-08-v1:`, no replacements.
- **Collectors.** Before: `2222a67` (PR #30, the audit's "after"). Candidate:
  `f8041a1` (`dev20`), with its source hashes recorded. One measurement
  adapter, from the candidate commit, for both.
- **Budgets.** The audit's two matched profiles: default (200 files, 4,000
  entries, depth 8, 5 s) and expanded (1,000 files, 10,000 entries, depth 16,
  30 s), both with 16 KB of excerpts and 2 KB of context.
- **Decision rule.** The candidate counts as an improvement on this sample
  only if, at the expanded profile, per-case wins exceed losses on hits
  including the map and total primary hits are not lower than before.

## Pool and acquisition, as they turned out

Fifteen of the 50 `test` rows had already been among the `dev` rows read on
November 7, so the pool held 25 rows, not 38. Twelve were selected; **13 stay
reserved**. All twelve base commits were fetched by shallow `git fetch` within
the caps (158 MB on disk), with no omissions. The
[selection record](../benchmarks/external-recall/frozen-dev20-2026-11-08/selection-record.json)
lists the ids only; no issue text is committed.

## Results

Paired by the strict comparer, twelve of twelve cases scored, 41 gold files.

| Profile | Level | Before hits | Candidate hits | Mean recall before → candidate | Wins / ties / losses |
| --- | --- | ---: | ---: | --- | --- |
| Default | primary | 10 | 14 | 31.5% → 50.3% | 4 / 7 / 1 |
| Default | with map | 21 | 23 | 61.8% → 70.6% | 3 / 7 / 2 |
| Expanded | primary | 12 | 15 | 35.2% → 53.1% | 4 / 6 / 2 |
| Expanded | with map | 23 | 26 | 65.5% → 77.0% | 3 / 7 / 2 |

At the expanded profile the candidate reaches at least one changed file in
12 of 12 cases, against 10 of 12 before.

**Registered decision: met.** At the expanded profile, wins on hits with the
map are 3 against 2 losses, and primary hits rose from 12 to 15.

**Wins** (expanded, hits with map): openbbterminal 0 → 2, both changed files
now primary; pip 1 → 3; dvc 0 → 1. Primary-only gains without a map-level
change: archivebox and modin.

**Losses** (expanded): sanic loses one file from the map while gaining one
excerpt; chalice drops from 5 to 4 at every level; netbox loses its single
primary hit, keeping it in the map. These are reported, not diagnosed: the
cases are now exposed, and reading them to explain the losses would make them
tuning material.

The pip case walked 434 files under the candidate against 780 before, because
`_vendor/` copies are now excluded, and still gained two files.

## What this establishes

On twelve cases authored outside this project, chosen by a rule fixed before
they were read, the November 7–8 collector changes deliver more changed files
to the brief than the PR #30 collector at both matched budgets, with two
case-level losses at each. It is the first frozen, held-out result in this
project that meets a pre-registered rule.

## What this does not establish

- Anything beyond twelve Python cases from one benchmark; a different sample
  could move the wins-against-losses margin, which is narrow (3 against 2).
- That the gold labels are complete; fixing-PR file lists are a relevance
  proxy, and absent paths stay in the denominators.
- Answer quality, host turns, tokens or cost; no model ran. Public benchmark
  cases may also be in cloud models' training data, which matters for any host
  comparison built on them, not for this collector-only measurement.
- That the 13 remaining reserved rows are untouched by other agents' work;
  they are unread by this project's runs as recorded here.
