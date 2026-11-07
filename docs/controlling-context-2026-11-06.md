# Controlling-context collection

Status: development candidate, November 6, 2026, `0.4.0.dev10`. The collector
now follows the four primary windows with bounded, software-selected context:
the top-level definitions those windows reference, one place where another file
uses a name they define, one test file that names them, and a path map of
matched files that were not excerpted. Nothing is interpreted; every addition
is an exact excerpt with its hash, labeled with the mechanical reason it was
added. This responds to the [host context cost analysis](host-context-cost-2026-11-06.md),
which found that the brief's omissions, not its size, left the host re-running
discovery. No cloud host and no local model were run for this record.

## What changed

`search.prepare` keeps its walk, scoring and primary selection unchanged, then
runs a context pass when `SearchLimits.context_bytes` is above zero (default
2,048 bytes; zero disables the pass and restores the previous output exactly).

1. **Definitions.** Identifiers used in the selected windows are looked up in a
   top-level definition index built during the walk: declaration keywords
   (`def`, `class`, `function`, `const`, `fn`, `struct` and similar) and
   leading-column assignments such as `DEFAULT_BACKEND = 'local'`. Names the
   request itself contains, language keywords and names already defined inside
   a selected window are skipped. Up to four definition windows of seven lines
   are added, most-used name first, preferring a definition in the referencing
   file, and clipped so they never repeat a line already excerpted.
2. **Usage.** For names the selected windows define, one window from the
   non-test file that uses the most of them, ranked by mention count.
3. **Test.** One window from the test-path file that names the most selected
   identifiers, centered on the first line naming the strongest one.
4. **Map.** Up to twelve matched-but-unexcerpted files as path, size and first
   non-empty line, highest lexical score first.

The packet cap rises from four to ten records (`collector.MAX_FILES`); primary
selection stays at four. New cutoffs are reported in the scan receipt:
`context_budget` (byte limit reached), `context_window_budget` (more candidates
than windows), `context_map_budget` and `definition_index_budget` (16,384
entries). Every context file is reread and its hash checked against the walk
before inclusion; `source_changed_after_search` still refuses a changed file.
Symlinks, denied names and unsupported extensions are excluded exactly as
before, since the pass only sees files the walk already read.

The brief marks each context excerpt with "Controlling context
(software-selected, not an interpretation)" and its reason, and lists the map
before the scan receipt. The workbench shows the same reason on each source
card, includes it in the exact-source JSON of the copied brief, and appends
the map after the source block. The local worker receives the context reasons
in its collection record; its evidence schema already enumerates whatever ids
the packet carries.

## Measured on the four exposed comparison fixtures

Generated with `benchmarks/native-preparation/generate.py` into a directory
outside the checkout; the same tasks the [native-retrieval comparison](native-preparation-2026-11-05.md)
ran. "Decisive files" are the grading keys' lists; a file counts when at least
one excerpt comes from it.

| Case | Excerpts | Excerpt bytes | Brief bytes | Decisive files excerpted | Map | Pass time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dispatch-path | 4 → 7 | 710 → 1,037 | 2,276 → 3,396 | 4/6 → 6/6 | 0 | 22 ms |
| publish-reorder | 4 → 7 | 728 → 1,112 | 2,331 → 3,697 | 4/7 → 6/7, `docs/contract.md` in map | 1 | 18 ms |
| two-log-failures | 4 → 7 | 737 → 1,105 | 2,348 → 5,099 | 3/6 → 6/6 | 12 (cutoff) | 21 ms |
| deployment-unknowns | 4 → 5 | 705 → 829 | 2,318 → 2,861 | 4/6 → 5/6, `receipts/readiness.json` in map | 1 | 18 ms |

What each case gained, against what the comparison record said the earlier
brief omitted:

- dispatch-path: `load_settings` (the `PARCEL_BACKEND` override) and
  `pick_backend` (the routing), both referenced from the selected `submit.py`
  lines, plus the one-line `LOCAL_TARGET` definition.
- publish-reorder: `journal.commit` and `notifications.send`, the two contracts
  the before/after `publish` bodies call, and the `Notifications` class the
  test constructs. The prose contract in `docs/contract.md` is mapped, not
  excerpted, because nothing in the selected windows names it.
- two-log-failures: `within_deadline` and `exhausted`, the two functions the
  failing assertions call, and `test_exhausted_at_limit`. The map is twelve
  utility files that match the broad request terms; the cutoff says more
  matched.
- deployment-unknowns: `app/settings.py`, reached as a use of `DEFAULT_MODE`,
  which the selected `config/defaults.py` defines. The readiness receipt is
  mapped only; its JSON has no identifier the windows share.

The largest brief grew from about 590 to about 1,270 tokens at four bytes per
token, and the worker's source message stayed under its 6,000-byte cap on all
four cases (2,992 to 4,068 bytes). The pass added 10 to 15 milliseconds.

## Program checks

189 Python tests pass under Python 3.12, six of them new: definition, usage
and test windows with their exact reasons; no duplicated or displaced primary
lines, including a definition window clipped before a primary window in the
same file; the byte cutoff and the zero setting; the map's contents; the
rendered labels and map section; secret and symlinked files staying out of
context. Node checks pass unchanged: 17 clipboard cases, frontend API smoke,
and 33 real-Chrome workbench scenarios with Python 3.12 and local Chrome 157.

## What this does not establish

- That the host takes fewer turns. That is the hypothesis the analysis set out;
  testing it needs this candidate frozen, person-authored fresh cases and a
  paired final-host run. The four fixtures above are exposed.
- Accuracy, savings or qualification of any model profile. No model ran.
- Behavior on real repositories: the definition regex is line-based and
  language-agnostic, so it will miss indented or decorated definitions and
  will index some non-definitions; the budget and labels bound the damage but
  the selection quality is unmeasured outside these fixtures.
- Primary selection is unchanged, including its known weakness of selecting
  an unrelated utility file when request terms are broad.
