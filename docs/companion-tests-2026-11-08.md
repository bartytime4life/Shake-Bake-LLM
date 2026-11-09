# Companion test files: rejected on fresh cases

Status: completed and reverted November 8, 2026. The protocol was pushed as
`8f5531d` before any row at `dev` offsets 1700 to 2299 was read
(`benchmarks/companion-tests-2026-11-08/protocol.json`). No model or host ran.

## Why it was tried

In the [draft comparison](draft-comparison-2026-11-08.md), the briefs held 9
of the 13 files the fixes changed, and three of the four misses were test
files. Across 45 exposed cases, the collector reached 70 of 100 changed files
counting the path map. Eight of the 30 misses were test files, and several
were named after a file the brief already showed:

- `test_option_parser.py` for `option_parser.py`;
- `test_util.py` for `util.py`;
- `util_test.py` for `util.py`.

## The candidate

The candidate was frozen as `2859128`. For each excerpted or mapped code file,
it listed the examined test file named after it, up to four in all:

- **Accepted names:** `test_x.py`, `x_test.py` or `parent_x_test.py`.
- **Among several:** the one sharing the longest directory prefix with the
  source file.
- **Where they went:** after the twelve-entry map, by path only.
- **Rendering:** the orientation brief attached each to its source file's row,
  and the evidence layout gave them their own section. They match nothing in
  the request, so they were not called matches.

The change was additive, so no excerpt or map entry could be lost. On the
exposed cases it reached 73 of 100 changed files instead of 70.

## Fresh result

Sixteen never-read multi-file cases were selected by the registered hash rule
from 600 rows: 257 were not multi-file, 136 failed the size rule and 19 came
from repositories used before. All sixteen checkouts were fetched (816 MB) and
none was omitted. Both commits were scored at default limits.

| | Baseline `8f8fde9` | Candidate `2859128` |
| --- | ---: | ---: |
| Changed files reached, excerpts plus map, of 44 | 30 | 31 |
| Changed files in excerpts | 19 | 19 |
| Cases gaining a file | | 1 (ggshield) |

- **Companions listed:** 31, of which one was a changed file.
- **Brief size:** orientation briefs grew by 0 to 285 bytes.
- **Decision:** the rule required more changed files on at least two cases.
  It was met on one, so the code is reverted.

## What this says

- **The naming link is real but rare:** a test named after a listed source
  file is a changed file about one time in thirty.
- **The gain on exposed cases did not carry over:** three companions paid off
  on the exposed cases, which were read while designing the rule. On the
  fresh cases, one did.
- **What the remaining misses are:** mostly source files with no lexical link
  to the issue text, such as netbox's serializers, dvc's remote backends and
  conan's `graph.py`. A name rule cannot reach them.

The run data is in `benchmarks/companion-tests-2026-11-08/`, in the files
`result.json`, `selection-record.json` and `acquisition.json`. It holds
per-case hits, brief sizes and receipt hashes, but no issue text. The
candidate and its revert both stay in this branch's history.
