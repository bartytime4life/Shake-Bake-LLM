# Primary selection on large trees: a rejected prior and two path fixes

Status: development change in `0.4.0.dev20`, November 8, 2026. The
[term-selection record](term-selection-2026-11-07.md) left one open point:
on the thirteen external Long Code Arena cases, excerpt-level recall had not
risen, and the working guess was that the four primary windows go to tests and
documentation that mention the request's names. That guess was tested first and
was wrong. No model or host ran.

## The rejected prior

When the request names code (a term with an underscore or a digit), test and
prose files were scored at 0.7 of their value in primary selection only.

| Set | Result |
| --- | --- |
| Task Lab, four fixtures | unchanged |
| Thirteen external cases, both limit profiles | unchanged on every case |
| Twelve self-commit cases | three cases lost hits, none gained |

The self-commit losses are expected, since those commits change docs and tests,
but the external cases are the ones that matter, and the prior moved none of
them. It was reverted.

## What actually fills the primary four on the misses

A per-case reading of the six external cases that missed or reached only the
map at the 5,000-file ceiling:

| Case | Primary four | Cause |
| --- | --- | --- |
| thealgorithms | a README and three unrelated solutions | The request writes `ProjectEuler`; the path is `Project Euler/`. Separator-insensitive path matching removed `_` and `-` but not spaces. |
| pipenv | four files under `patched/notpip/_vendor/` | Vendored third-party copies outscored the project's own code. `vendor/` was excluded; pip's `_vendor/` convention was not. |
| keras | four `keras/engine/` files | The traceback names engine functions; the changed module appears only in the title. Map rank 2. |
| rich | `console.py`, its test, `CHANGELOG.md`, `style.py` | The traceback again; the fix is in `__init__.py`. Map rank 12. |
| ccxt | exchange base classes and a test | Same pattern. Not reached. |
| spacy | a C header, an English lemmatizer, a README, a test | `Hindi` never matches the path `lang/hi/`. Not reached. |

Tests and docs are a minority of these primaries; tracebacks and path
conventions are the pattern.

## The two fixes

- Path matching also removes spaces, so `ProjectEuler` matches
  `Project Euler/Problem 01/sol2.py`.
- `_vendor` joins `vendor` in the excluded directories; skipped files are
  counted under `excluded_directory` as before.

| Set | `dev19` | `dev20` |
| --- | --- | --- |
| Task Lab | 10/10 | 10/10 |
| Four fixtures, decisive files | 6/6, 6/7+1, 6/6, 5/6+1 | unchanged |
| Twelve self-commit cases | 15.2% primary, 19.4% excerpted | unchanged on every case |
| External, 1,000 files: recall primary / with map; cases reached | 42.3% / 69.2%; 9/13 | 50.0% / 76.9%; 10/13 |
| External, 5,000 files: recall primary / with map; cases reached | 46.2% / 76.9%; 10/13 | 53.8% / 84.6%; 11/13 |

Per case, two improve and none regress: pipenv's changed file moves from the
map into the primary four, and thealgorithms is reached for the first time.
Receipts are under `examples/receipts/primary-selection-2026-11-08/`.

## What is left, and why it is not attempted here

The remaining pattern is a traceback in the issue body that names framework
internals while the fix is elsewhere (keras, rich, ccxt). Down-weighting
traceback lines would be a reasonable next candidate, but it would be designed
by reading these same exposed cases. It belongs to the frozen-candidate step
with fresh cases, not to another round of tuning here. Spacy needs language
knowledge (`Hindi` → `hi`) that a lexical collector does not have.

## Program checks

237 Python tests pass, one new: a path with spaces is matched by its compact
term, and a `_vendor/` copy is excluded while the project's own file is kept.

## What this does not establish

- Anything on the unread `test` split; these thirteen cases are exposed and
  have now shaped three changes, so their figures are development evidence.
- Answer quality or host turns; no model ran.
