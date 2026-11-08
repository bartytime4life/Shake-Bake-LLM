# Embedding rerank of candidate windows

Status: mechanism built and tested in `0.4.0.dev14`; development trial run in
`0.4.0.dev16` with `qwen3-embedding:0.6b` after the owner approved the pull
(result below: mixed, the option stays off by default). This is candidate C4
from the [November 6 web research](research-2026-11-06.md):
the first use of the local model whose effect is checked mechanically (which
windows end up in the brief) rather than read by a person. It is optional,
explicitly enabled, and adds no window the lexical scan did not find.

## What it does

`search.prepare` accepts a `scorer(request, texts) -> similarities`. When one
is given, the top `MAX_POOL = 24` lexical candidate windows are scored and
reordered by similarity to the request before primary selection; candidates
beyond the pool keep their lexical order behind it, and the receipt reports
`rerank_pool_budget` when any were left out. The one-window-per-file-first rule
still applies, so the rerank chooses which files' best windows lead, and the
lexical score breaks ties. The controlling-context pass then runs on the
reranked primary set as before.

`rerank.EmbeddingScorer(model, port, seconds)` is the scorer for a loopback
Ollama embedding model. It checks the model's metadata is local, records the
runtime version, posts scoring copies in batches of up to eight inputs to
`/api/embed` with `keep_alive: 0` and server-side `truncate: False`, and refuses
a remote response, a model mismatch, a wrong vector count, a wrong or
non-finite dimension, or a zero vector. Request and window scoring copies are
limited to 4,096 UTF-8 bytes; an incomplete trailing character is dropped only
from that copy. Exact excerpts and the original request remain unchanged.
Metadata, runtime lookup and all batches share one deadline. Similarities are cosines computed here, not
trusted from the server. A refusal never hides evidence: `prepare` keeps the
lexical order and records the refusal code in `SearchResult.rerank`; a
successful rerank records the model, pool and candidate counts, whether the
order changed, the rounded similarities, dimensions, reported usage and
elapsed time. The brief's scan receipt labels the outcome as a scan fact about
ordering and also reports attempted requests, complete responses and scoring
copy truncation. Counts and elapsed time are invocation-local, including when
the scorer is reused and a later case fails. See the receipt definitions below.

Enabled with `--rerank-model` on the CLI brief, the Task Lab runner and the
external recall adapter; the workbench is not wired yet. Nothing is downloaded;
the model must already be installed.

## Program checks

The original four tests run a loopback stub embedding server whose vectors point one way
when a text contains a marker and the other way otherwise: the rerank moves the
marker file to the front without adding or dropping windows and sends exactly
the request plus the pool; each refusal (remote metadata, model mismatch, count
mismatch, bad dimension) falls back to the lexical order with its code
recorded; the pool is capped at 24 with the cutoff disclosed; and the rendered
brief carries the scan-fact line for both the success and the refusal. PR #35
reported 204 Python tests; that historical count is not a new model qualification.

The follow-up adds synthetic regressions for the full 24-window pool at 1,024
dimensions, correct cross-batch vector alignment, Unicode scoring truncation
with exact evidence hashes, reused-scorer success/failure/recovery, a malformed
second batch, an aggregate network deadline, a high-dimensional response above
the unchanged transport cap, a remote embedding response and off-by-default
construction. A synthetic recall-adapter check verifies exported per-case
telemetry after a reused scorer fails. The stub now identifies the query by
text, instead of incorrectly treating each batch's first input as the query.

### Receipt definitions and remaining acceptance evidence

- `embed_calls`: embedding POST attempts dispatched to the bounded transport;
  includes a call whose response times out or is refused.
- `embed_calls_completed`: attempts for which the transport returned a parsed
  JSON object. Its model, vector count or contents may still be refused.
- `windows_scored`: windows in a successfully completed cosine-scoring call;
  zero after any scorer refusal. Partial vectors never determine selection.
- `truncated_windows` and `request_truncated`: shortening of this invocation's
  scoring copies, computed before source is sent; preserved on later failure.
- `local_server_reported_usage`: accepted per-batch usage accumulated during
  this invocation only; partial on failure, not a complete task measurement.
- `elapsed_seconds` and `error`: this invocation's elapsed time and refusal,
  never fields retained from a previous case. Successful recovery removes the
  previous error. The deadline covers network waiting across all requests;
  bounded local encoding, parsing and cosine computation are not a hard
  real-time guarantee.

The fixed batch size is qualified here only by synthetic transport tests and
the historical 1,024-dimensional trial. Larger allowed dimensions can still
exceed 256 KiB and must visibly fall back; the cap is not increased.

Historical JSON receipts below are preserved. All twelve self-commit rerank
rows omit the new batch/truncation counters and identify `dev15`, so they do not
directly verify the final source's real-model truncation path. Their generic
adapter warning incorrectly says the cases were authored outside this project;
these are the collector authors' own development commits. They are not part
of the [independent retrieval evaluation](independent-retrieval-2026-11-07.md).

Before experimental acceptance, obtain explicit approval for a bounded trial
using the already-installed embedding model and exact reviewed source. Retain
source/model identity, runtime version, a full 24-window pool, an oversized
Unicode window, per-batch response bytes, attempts, truncation and deadline
results, source hash preservation and a visible refusal/fallback case. No such
real-model follow-up was run for this receipt correction. Model reuse and
lexical/embedding blending remain separate, unexecuted experiments.

## Development trial with `qwen3-embedding:0.6b`

The owner's Ollama served no embedding model (the installed chat models return
"This server does not support embeddings"), so the trial waited for an
explicit pull, which the owner approved. `qwen3-embedding:0.6b` (639 MB, 1,024
dimensions) was pulled on November 7 and three runs followed, all local, no
cloud, with the `dev15` collector. Receipts are under
`examples/receipts/embedding-rerank-2026-11-07/`.

**Two defects surfaced and were fixed first.** A full pool of 24 vectors is
about 320 KB of JSON and exceeded the worker transport's 256 KB response cap,
so every large-pool rerank had quietly fallen back to lexical order with
`worker_response_too_large` recorded; the scorer now embeds in batches of
eight under one deadline and records `embed_calls`. A window over 4,096 bytes
had refused the whole rerank; since the copy only orders, it is now cut for
scoring and counted as `truncated_windows`, with the exact excerpt untouched.
The first self-commit run hit both; the numbers below are from the rerun.

**Task Lab, evidence only.** 10/10 required spans with the rerank. Pools were
two to four windows; the order changed in four cases (repo-tour, runtime-mode,
unknown-hardware, coverage-budget). Each case spent about 1.5 seconds in the
embed call.

**Four comparison fixtures, decisive files excerpted, lexical → rerank:**

| Case | Decisive files | Order | Embed |
| --- | ---: | --- | ---: |
| dispatch-path | 6/6 → 6/6 | changed (submit before the test) | 3.1 s, 2 calls |
| publish-reorder | 6/7 → 7/7 | `docs/contract.md` promoted into the primary four | 3.1 s, 2 calls |
| two-log-failures | 6/6 → 6/6 | changed (README first) | 1.6 s |
| deployment-unknowns | 5/6 → 5/6 | `receipts/readiness.json` promoted, `app/transport.py` demoted out of the four | 1.6 s |

The one clear gain is the prose contract in the publish case, which the
lexical order left in the map. The rerank also tends to lift README-style
prose toward the top, which matches the request's wording rather than its
code.

**Twelve self-commit cases** (the collector authors' own commits, mostly
documentation; direction only):

| Measure | Lexical | Rerank |
| --- | ---: | ---: |
| Mean recall, four primary excerpts | 12.9% | 13.8% |
| Mean recall, all excerpts | 18.6% | 18.6% |
| Mean recall, excerpts plus map | 38.3% | 41.6% |
| Cases with any changed file in the primary four | 9/12 | 8/12 |
| Cases with any changed file in excerpts | 9/12 | 11/12 |
| Per-case excerpted hits | – | up 4, down 7, same 1 |
| Embedding time per case | – | 6.8 to 7.3 s |

More cases reach at least one changed file, while cases that were already
well served lose hits: the rerank spreads coverage rather than deepening it.
The all-excerpt macro mean actually falls slightly, from 18.637% to 18.567%,
which the one-decimal display hides. Total primary changed-file hits fall from
18 to 12 and all-excerpt hits from 26 to 19; macro recall weights each case
equally even when their changed-file counts differ. Mean recorded total
preparation time rises from 0.062 seconds to 7.118 seconds. These are paired
historical single runs, not repeated latency measurements or answer accuracy.
The time cost is the larger finding. The scorer sends `keep_alive: 0` like the
worker, so Ollama unloads the 0.6B model after every call and reloads it for
the next, which is most of the 1.5 seconds per call; a repository-sized pool
needs two to four calls.

**Decision.** The option stays off by default and is not wired into the
workbench. The mechanism works and is now measurable; the ordering it
produces is not yet a clear improvement on this material, and the per-case
cost is seconds, not milliseconds. Two bounded follow-ups would make a second
trial fair: a short keep-alive scoped to one preparation so the batches share
one model load, and combining similarity with the lexical score instead of
replacing it, so a weak prose match cannot displace a strong identifier match.
Either is a new candidate to measure, not a tune on these exposed cases.

## What this does not establish

- Selection quality on unseen cases; the Task Lab and fixtures are exposed and
  the self-commit cases are the authors' own, mostly documentation commits.
- Behavior with the local worker enabled on top of the rerank; the two are
  independent stages and were not run together.
- Workbench integration; the GUI and MCP paths call `build_brief` without a
  rerank model.
- Anything about other embedding models or dimensions; one 0.6B model at
  1,024 dimensions was run, with the model unloaded between calls.
