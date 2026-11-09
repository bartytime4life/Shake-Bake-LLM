# Current-main integration — November 9, 2026

The [initial improvement pass](project-improvements-2026-11-09.md) used an
isolated `0.4.0.dev8` snapshot at `f9753fb`. Before publication, GitHub main was
refreshed and found to contain 71 newer commits through `2a3a953`, with source
version `0.4.0.dev23`. The improvements were merged with that current source
rather than replacing its newer behavior. The original owner checkout and its
twenty preexisting changed/new files remain untouched.

## Resulting behavior

- Browser task drafts can be kept only in the current page or cleared while
  preserving a prepared brief. Cross-tab opt-out, initialization races and
  storage failures retain their explicit handling.
- Non-UTF-8 filename bytes are refused and disclosed without invalidating other
  usable evidence. Valid Unicode remains exact. Main's existing rejection of
  filename control characters is preserved.
- GUI/shared/owned-runner serialized requests share the 128 KiB limit. Runner
  results share a 1 MiB limit including the newline, and the shared response
  allows its bounded envelope. Ordinary Ollama input/response limits and the
  current main worker settings remain unchanged.
- Source display uses the collector's line boundaries. Handoff and JSON export
  preserve exact captured text, including CR and Unicode separators.
- The offline host-review tool binds declared judgments to receipt and answer
  identities, including byte-identical answers in different attempts. It
  preserves unknown judgments, failed/unstarted attempts and missing usage.
- First-use and recovery instructions are linked from the README, and the
  result reminds users to save an export because session history is temporary.

Main's BM25-style selection, signal-based request terms, controlling context,
optional reranking, context map, matching-line index, orientation handoff,
fenced untrusted model draft and fitted worker source view are retained. The
helper still accepts the current ten-record evidence boundary and fetches its
later records. The new protocol module participates in pipeline identity.

The development-only change-review code and dated synthetic/public aggregate
records are also retained. They are outside normal GUI/CLI/MCP routing. Their
historical frozen trial records describe their original revisions; the merge
does not rerun, regrade, qualify or reproduce those earlier model/host trials.

## Verification

| Check | Result |
| --- | --- |
| Source program suite, Python 3.12 | 289 passed |
| Source program suite, Python 3.14 | 289 passed |
| Source JavaScript | Syntax and 69 lightweight checks passed |
| Source browser | 41 workbench, 14 readiness and 5 clipboard scenarios passed |
| Synthetic selection and evidence-only Task Lab | Both selection variants and all ten cases retained required source spans |
| Wheel inspection | Code, web/demo assets and legal notices match current source; no core runtime dependencies |
| Isolated installed Python 3.12 package | 289 program tests and demo/shared/preference smoke passed |
| Installed browser | The same 60 workbench/readiness/clipboard scenarios passed |

Hosted CI is reported separately on the pull request. The local
browser checks use isolated Chrome profiles and synthetic source, with
simulated readiness/failure responses. Program tests do not qualify real model
accuracy, independent security, broader host delivery, all browsers or
whole-task savings. No real model/host trial or private-source handoff was
performed for this repository update.

## Publication boundary

The repository update uses a dedicated review branch. It does not replace the
running installed preview, deploy a website, change operational settings or
promote a model. Source, benchmark scripts, documentation and reviewed
synthetic/public aggregate records are selected for publication; local
configuration, private captures, state directories, credentials, environments
and build outputs remain excluded. A scoped pre-publication review found no
prohibited artifacts among the selected files.

The initial local commit is `7f20fe5`. The review branch contains an explicit
merge of current main so the original local work and newer upstream history
remain recoverable. Hosted checks on the pull request are a separate gate;
local results do not imply a successful GitHub run or a merge into main.
