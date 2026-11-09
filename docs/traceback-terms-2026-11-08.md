# Demoting stack-trace words: rejected during development

Recorded November 8, 2026. No code change ships, and no fresh run was spent,
because the candidate lost on the development cases. No model or host ran.

## The idea

Earlier records described one pattern behind the collector's misses. A
traceback in the issue names framework internals, while the fix is elsewhere
([primary-selection record](primary-selection-2026-11-08.md)): keras, rich and
ccxt. The candidate changed how the request's search terms are ranked:

1. **All frames.** A word that appeared only in stack-trace frame lines ranked
   after every other word. Those lines are the Python `File "…", line N` lines
   with the source line printed after each, and JavaScript `at …` lines.
2. **Third-party frames only.** The same demotion applied only to frames whose
   path looked third-party: `site-packages`, `dist-packages`, a standard
   library directory, `<frozen …>` or `node_modules`.

The exception message line kept its weight in both versions.

## Development result

Both versions were scored against `main` (`8f8fde9`) on the 61 exposed cases
with local checkouts, at default limits. Those cases hold 144 changed files.

| | `main` | All frames | Third-party frames |
| --- | ---: | ---: | ---: |
| Changed files reached, excerpts plus map | 100 | 97 | 97 |
| Changed files in the four primary excerpts | 57 | 53 | 54 |

- **Gains:** in each version, one case gained (conan, two files).
- **Losses:** six cases lost, including pip, rich, pre-commit and pyocd.

## Why it fails

Stack traces in these issues often run through the very code that needs the
fix. A user's traceback shows the project's own package installed under
`site-packages`, so a path cannot tell the project's own frames from a
library's. In pip, the words from frames under `site-packages/pip/_internal/`
were the ones that found the changed files.

## What follows

The candidate was not frozen, and no fresh rows were read for it. The lexical
collector now appears close to its limit on this material:

- **Companion test files:** rejected on fresh cases
  ([record](companion-tests-2026-11-08.md)).
- **Stack-trace demotion:** loses on development cases (this record).
- **Remaining misses:** mostly source files with no word in common with the
  issue text.
