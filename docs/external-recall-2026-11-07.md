# External file recall: thirteen Long Code Arena bug-localization cases

Status: first run of the collector on cases this project did not author,
November 7, 2026, with the `0.4.0.dev17` collector. Development split only;
the `test` split stays unread until the collector is frozen. No model answered
anything: the only model involved is the optional embedding rerank, and it
chose order, not content. File-level recall measures the collector, not a
cloud host and not any answer.

## Material and method

Dataset: `JetBrains-Research/lca-bug-localization` on Hugging Face (Apache-2.0,
not gated, revision `f2bb26a1…`), Python config, `dev` split, 4,339 rows. Each
row is a real GitHub issue paired with the pull request that fixed it, with
the repository, the base commit and the changed files. The bundled repository
archives total 11 GB for Python alone, so instead each chosen case's base
commit was shallow-fetched from GitHub (`git fetch --depth 1 … <base_sha>`),
963 MB for thirteen checkouts, all outside this checkout.

Selection was fixed before any run: the first 300 rows in dataset order; a
permissive repository license (MIT, Apache-2.0, BSD, ISC, MPL-2.0); 50 to
1,500 non-test files; at most ten changed files; one case per repository. The
first 300 rows hold only 13 distinct repositories that pass (276 rows were
further cases of the same repositories, 11 were out of the size range), so
the sample is 13, not the 24 intended. The request is the issue title, a blank
line and the issue body, exactly as the dataset gives them. The manifest with
every case's repository, base commit, license, changed files and issue URL is
`examples/receipts/external-recall-2026-11-07/cases-manifest.json`; the three
receipts sit beside it.

## Results

| Run | Mean recall, primary four | Mean recall, all excerpts | Mean recall, with map | Cases reaching any changed file | Cases hitting the file budget |
| --- | ---: | ---: | ---: | ---: | ---: |
| Default limits (200 files, 5 s) | 23.1% | 26.9% | 34.6% | 5/13 | 13/13 |
| Ceiling limits (1,000 files, 30 s) | 46.2% | 50.0% | 53.8% | 7/13 | 4/13 |
| Ceiling limits, blended rerank | 46.2% | 50.0% | 53.8% | 7/13 | 4/13 |

Per case at the ceiling, seven cases reach at least one changed file in the
excerpts (mitmproxy, colossalai, deepspeed, pytorch-image-models, lightning,
jax, pipenv) and six reach none at any level (thealgorithms, keras, rich, ccxt,
spacy, streamlit). The rerank moved one primary hit from deepspeed to jax and
left every mean unchanged; it cost 1.6 to 2.1 seconds per case. The
matched-line index reached no file the map had not, as on the self-commit
cases.

## What the run shows about the collector

1. **The default walk budget is the first limit on real repositories.** Every
   case hit `file_budget` at the shipped defaults, and recall doubled when the
   limit rose to its ceiling. Four repositories (ccxt, streamlit, colossalai,
   lightning) exceed even the 1,000-file ceiling, so part of each tree was
   never read; two of those four miss entirely.
2. **The 16-term request cap binds on every case and keeps the wrong words.**
   Terms are taken in order of first appearance, so a long issue contributes
   its template ("system", "information", "describe", "https", "github",
   "com") and drops 120 to 220 later words, often the identifiers. In the
   keras case the request yields `mobilenetv3`, `models`, `can`, `infer` …
   `script`, `provided`, and the changed file is `mobilenet_v3.py`; in the
   streamlit case `cache_data` survives but `hashing`, the changed module,
   does not. This is the collector's own doing and the clearest next
   candidate: choose terms by signal (identifier shape, rarity, presence in
   the title) rather than by position, and drop URL fragments.
3. **The controlling-context and line-index budgets are reached on every
   case**, which is expected on real trees: the pass is bounded by design, and
   the receipt says so.
4. **The blended rerank is neutral here too.** With the pool drawn from the
   same lexical candidates, a better ordering cannot rescue a case the terms
   never reached.

## What this does not establish

- A held-out number: the `dev` split is development material and these 13
  cases are now exposed; the `test` split (0.18 MB, unread) is for after the
  collector is frozen.
- Anything about answer quality, host turns or the drafted prompt; no host
  and no chat model ran.
- Behavior on Java or Kotlin, on the 35 repositories not sampled, or on
  repositories above the ceiling; the sample is small and one case per
  repository.
- Public datasets may be in cloud models' training data; that does not affect
  this collector-only measurement but would affect any host comparison built
  on the same cases.
