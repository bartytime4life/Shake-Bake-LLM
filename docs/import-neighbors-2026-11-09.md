# Import neighbors: rejected during development

Recorded November 9, 2026. No code change ships and no fresh rows were read.
No model or host ran.

## The idea

After two lexical candidates failed, the next signal tried was structural,
not lexical. Many of the collector's misses are project modules that a
selected file imports, though the issue never names them. Examples are conan's
`graph.py` and sanic's `http.py`.

The candidate parsed `import` and `from … import` statements in Python files,
resolving relative imports. It then listed project modules imported by the
four primary files, after the map and by path only.

## Development result

Each version was scored against `main` (`8f8fde9`) on the 61 exposed cases,
which hold 144 changed files. The changed files reached, counting excerpts and
the map, were:

| Version | Reached | Cases changed |
| --- | ---: | ---: |
| `main` | 100 | |
| Importers and imported modules, up to four | 103 | 3 gained |
| Imported modules only, up to two | 104 | 4 gained |
| The same, with the import parser fixed | 101 | 1 gained |
| The same, ranked by how many imported names the excerpts use | 101 | 1 gained |

- **The bug:** the apparent gain of four files came from a parsing error. The
  first pattern let a name list run onto the next line and dropped many
  imports.
- **Why the bug mattered:** with fewer imports seen, fewer modules competed
  for the two slots, so the right ones happened to surface.
- **After the fix:** the right modules ranked second to fifth among 3 to 23
  imported modules per case, with nothing structural to put them first.
- **The usage signal:** ranking by whether the excerpts actually use a
  module's imported names did not change that.
- **How the bug was caught:** a unit test written before freezing, which is
  why the fix came before any fresh check.

The first version listed 199 neighbors for its 3 changed files, about 1.5%
precision. The two-slot version listed 102 neighbors.

## What follows

The candidate was not frozen and is reverted. Together with the
[companion tests](companion-tests-2026-11-08.md) and the
[stack-trace demotion](traceback-terms-2026-11-08.md), three cheap
collector signals have now failed. The changed files the collector misses do
sit near what it finds, but among many equally near files. Telling them apart
takes reading the code, which is the host's job. That is an argument for the
orientation framing, which tells the host to follow callers and related
modules, rather than for more collector rules.
