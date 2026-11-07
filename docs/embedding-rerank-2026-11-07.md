# Embedding rerank of candidate windows

Status: mechanism built and tested, November 7, 2026, `0.4.0.dev14`; no model
trial yet. This is candidate C4 from the [November 6 web research](research-2026-11-06.md):
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
runtime version, posts the request and the window texts to `/api/embed` with
`keep_alive: 0` and no truncation, and refuses a remote response, a model
mismatch, a wrong vector count, a wrong or non-finite dimension, a zero vector
or a window over 4,096 bytes. Similarities are cosines computed here, not
trusted from the server. A refusal never hides evidence: `prepare` keeps the
lexical order and records the refusal code in `SearchResult.rerank`; a
successful rerank records the model, pool and candidate counts, whether the
order changed, the rounded similarities, dimensions, reported usage and
elapsed time. The brief's scan receipt states the outcome in one line, labeled
a scan fact about ordering.

Enabled with `--rerank-model` on the CLI brief, the Task Lab runner and the
external recall adapter; the workbench is not wired yet. Nothing is downloaded;
the model must already be installed.

## Program checks

Four new tests run a loopback stub embedding server whose vectors point one way
when a text contains a marker and the other way otherwise: the rerank moves the
marker file to the front without adding or dropping windows and sends exactly
the request plus the pool; each refusal (remote metadata, model mismatch, count
mismatch, bad dimension) falls back to the lexical order with its code
recorded; the pool is capped at 24 with the cutoff disclosed; and the rendered
brief carries the scan-fact line for both the success and the refusal. 201
Python tests pass.

## Why no trial is recorded here

The owner's Ollama serves no embedding model: `/api/embed` with the installed
chat models returns "This server does not support embeddings". The project
rule forbids automatic downloads, so the trial waits on an explicit pull. The
smallest fit is `qwen3-embedding:0.6b` (about 640 MB, 1,024 dimensions, from
the Ollama library). Once installed, the trial is three commands and needs no
cloud:

```bash
python3.12 -B benchmarks/run_task_lab.py --evidence-only --rerank-model qwen3-embedding:0.6b --output /abs/out/tasklab-rerank.json
python3.12 -B benchmarks/external_recall.py --cases /abs/cases.jsonl --repos /abs/repos --rerank-model qwen3-embedding:0.6b --output /abs/out/recall-rerank.json
python3.12 -B -m shake_bake brief --root <fixture> --task "<task>" --rerank-model qwen3-embedding:0.6b
```

What it will measure: Task Lab required-span coverage (must stay 10/10),
decisive-file coverage on the four comparison fixtures, and file recall on the
self-commit cases against the lexical-only receipts already retained under
`examples/receipts/retrieval-scoring-2026-11-07/`, plus per-case embedding
time. A gain on those is development evidence for the candidate; qualification
still needs a reserved cohort, and the rerank never promotes a model.

## What this does not establish

- Any effect on selection quality; no embedding model has run.
- Behavior with the local worker enabled on top of the rerank; the two are
  independent stages and were not run together.
- Workbench integration; the GUI and MCP paths call `build_brief` without a
  rerank model.
