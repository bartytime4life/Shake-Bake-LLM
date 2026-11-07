# Independent retrieval audit: limited gains and retained regressions

November 7, 2026 follow-up to [PR #30](https://github.com/bartytime4life/Shake-Bake-LLM/pull/30).
Nine independently authored software-localization cases were evaluated with
frozen collector implementations and identical collection budgets. Average
primary recall rose, but expanded primary hits stayed **4/17**, with two
case-level gains and two losses. Excerpts plus map reached **9/17** files,
versus **6/17** before. This is a bounded Python subset, not a benchmark-wide
estimate or a model-accuracy, ChatGPT/Claude usage or cloud-cost result.

The [original scoring report](retrieval-scoring-2026-11-07.md) remains a
historical development record. Its twelve mostly documentation-oriented
self-commit cases are not part of this independent cohort. Both historical
self-commit receipts label `helper_version` as `0.4.0.dev10`; filenames alone
do not identify their scoring implementation. This audit pins commit/source
identities instead of treating a version string as proof.

## Inputs and licensing

- Dataset: JetBrains Research [Long Code Arena bug localization](https://huggingface.co/datasets/JetBrains-Research/lca-bug-localization), Python `test` split.
- Revision: `f2bb26a1c3320ccc1d7b02d2630077ff327a80f6`.
- File: `py/test-00000-of-00001.parquet`, 175,518 bytes; SHA-256 `96c06c997caa3dc63831302db2c19a1d8273384049dafdffe49f1bbcc133410f`.
- Before collector: `2a0acdf4a4e3e70ee2dd1ab116826fdc04506295`.
- PR #30 collector: `2222a67d4289a18abfb2305b9a62f5c9ab36c547`.

The dataset card declares Apache-2.0. Original source licenses were checked
at the recorded base commits, and license-file hashes were rechecked against
the materialized snapshots. The nine source repositories declare MIT or
Apache-2.0; their licenses and notices remain applicable. The benchmark
[maintainers' publication terms](https://huggingface.co/spaces/JetBrains-Research/long-code-arena/blob/fd11dec2f9fea2a14d0e35c9543674797da0252d/src/tasks_content.py)
require resulting research publications to be open access. This openly
accessible report records those terms without replacing third-party licenses.
Attribution: Bogomolov et al., [Long Code Arena: a Set of Benchmarks for
Long-Context Code Models (2024)](https://arxiv.org/abs/2406.11612).

Twelve IDs were selected before inspecting their task content by sorting
`sha256("shake-bake-independent-pilot-2026-11-07-v1:" + text_id)`; no replacement
cases were used. Nine complete snapshots were scored. Pulumi, Textual and
Plotly remained unscored under the 20 MiB per-archive cap. Their omissions
are disclosed rather than turned into zero-score cases or silently replaced.

The approved continuation allowed 100 MiB compressed transfer and 1 GiB
expanded data, with a 20 MiB per-archive cap. Actual continuation transfer was
86,001,366 bytes, including aborted oversize attempts. The nine ready trees
contain 79,462,840 regular-file bytes. Wekan and PaddleSpeech initially failed
the no-links materializer; a separately frozen link-preserving materializer
reused their already-downloaded archives, with **zero additional transfer**.
It validated paths/link graphs before writing, preserved links without reading
through them, and left the collector's symlink refusals intact.

The [manifest](../benchmarks/external-recall/independent-2026-11-07/manifest.json)
retains all twelve dispositions, base commits, available archive sizes/hashes,
corpus identities, exact request hashes, relevance paths and license identities.
It contains no issue bodies or source excerpts. Gold paths come from the
dataset's fixing-PR labels and are an imperfect relevance proxy; absent or
excluded paths remain in the scored cases' denominators.

Scoring/query code and budgets were frozen before these cases were inspected.
Seven were evaluated first; the nine-case result adds the two link-bearing
snapshots and reproduces the earlier seven file-level outcomes. Subsequent
replays and filter diagnostics use already-exposed cases, not new independent
samples. The other 38 Python test cases remain reserved. LCA `dev` includes
`test`, so these splits must not be treated as disjoint tuning/evaluation sets.

## Matched-budget results

No reranker or model was used. Four primary windows, 16,384 excerpt bytes and
2,048 controlling-context bytes were retained for both implementations.

| Profile | Files / entries / depth | Deadline |
| --- | --- | --- |
| Default | 200 / 4,000 / 8 | 5 seconds |
| Expanded | 1,000 / 10,000 / 16 | 30 seconds |

| Profile and recall level | Before mean | PR #30 mean | Before total hits | PR #30 total hits |
| --- | ---: | ---: | ---: | ---: |
| Default primary | 5.56% | 16.67% | 1/17 | 2/17 |
| Default all excerpts | 5.56% | 16.67% | 1/17 | 2/17 |
| Default excerpts + map | 16.67% | 22.22% | 2/17 | 3/17 |
| Expanded primary | 20.37% | 33.33% | 4/17 | 4/17 |
| Expanded all excerpts | 20.37% | 38.89% | 4/17 | 5/17 |
| Expanded excerpts + map | 42.59% | 62.04% | 6/17 | 9/17 |

Mean recall weights each task equally. Total hits weight every supplied
relevant path equally: expanded primary micro recall stayed 4/17 (23.53%).
Neither aggregation should be substituted for the other.

| Expanded case | Gold files | Primary before → after | All excerpts | Excerpts + map |
| --- | ---: | ---: | ---: | ---: |
| Datasets | 2 | 1 → 0 | 1 → 1 | 1 → 1 |
| Keras | 1 | 0 → 0 | 0 → 0 | 0 → 0 |
| Rasa | 3 | 1 → 0 | 1 → 0 | 1 → 1 |
| Wekan | 1 | 0 → 0 | 0 → 0 | 0 → 1 |
| ControlNet | 1 | 0 → 1 | 0 → 1 | 1 → 1 |
| Beets | 2 | 0 → 0 | 0 → 0 | 0 → 1 |
| JAX | 1 | 0 → 1 | 0 → 1 | 1 → 1 |
| Faker | 2 | 2 → 2 | 2 → 2 | 2 → 2 |
| PaddleSpeech | 4 | 0 → 0 | 0 → 0 | 0 → 1 |

The two primary gains coexist with two regressions and five ties. The
Datasets file remained in controlling context; the Rasa file remained in the
map. The PR #30 change includes file scoring, IDF-weighted window placement
and filtering; this comparison does not isolate the BM25 formula alone.

## Exclusions, truncation and processing time

The default walk hit `file_budget` in **7/9** cases. Expanded collection still
hit it in PaddleSpeech (**1/9**), leaving its relevant
`paddlespeech/vector/exps/ge2e/audio_processor.py` unexamined. All nine requests
exceeded the unchanged sixteen-term query cap. No run hit its time deadline.

`src/datasets/arrow_dataset.py` is 276,317 bytes, above the unchanged 262,144-byte
source-file limit, and was refused in both arms. A different limitation was
observed in expanded PaddleSpeech: the relevant
`paddlespeech/s2t/transform/spectrogram.py` was matched by the old scorer and
excluded by PR #30 as `low_signal_match`. Neither arm delivered that file in
excerpts or map. Thus the filter did remove a supplied relevant file, without
an observed loss of delivered coverage for that path.

| Five-repeat timing series | Before, ms | PR #30, ms |
| --- | ---: | ---: |
| Default | 170.4 | 127.8 |
| Expanded | 301.5 | 223.3 |

These are medians of nine case medians, five untraced prepare calls after one
warmup, with rotating arm order. Imports, network, corpus hashing and tracing
are excluded. Repeated selections were stable, diagnostics matched ordinary
calls, and corpus hashes matched before/after. This is warm-cache timing on
one evaluation machine; cache/runtime noise and brief concurrent receipt
preparation limit causal timing claims. It is not owner-PC or end-to-end
assistant latency. A separately frozen observed-main navigation index had an
additional output budget and is excluded from the matched excerpt/map result.

## Exposed-case filter ablation

A later diagnostic changed only `DISTRACTOR_RATIO = 0.2` to `0.0` in a local
PR #30 copy. With nonnegative scores and the strict less-than condition, zero
disables filtering. BM25 scoring, window placement, request text and all source
protections/budgets were unchanged. This was not installed or promoted.

Across all eighteen case/profile pairs, disabling the filter changed **no
gold-file primary, all-excerpt or map hit count** and repaired neither primary
regression. The relevant PaddleSpeech file's score was 1.312224 against a best
score of 26.876657 (4.88%). Its only matched terms, `but` and `paddlepaddle`,
occurred in 508 and 530 of 1,000 examined text files. The exclusion followed
the declared heuristic. Without filtering, it ranked 549th and was still not
delivered. Other, non-gold map paths changed in one default-budget case.

Filter-on/off median case times were 123.7/128.0 ms at default limits and
232.0/258.6 ms expanded, using a separate five-repeat timing series. All 36
arm/profile results were stable and trace-matched; the filter-on control
reproduced the saved nine-case file outcomes. These exposed diagnostics do
not validate a new scorer or justify a general safety/accuracy claim.

## Executable replay and preserved receipts

The [audit summary](../benchmarks/external-recall/independent-2026-11-07/audit-summary.json)
retains per-case gold status, hits, exclusions, cutoffs and all five timing
samples. It is a labeled derived audit, not a native adapter schema-2 receipt.
Its raw audit/evaluator/wrapper hashes are retained for provenance.

The following native schema-2 receipts are **known-case accounting replays**
through measurement commit `9361d028d836d561cd2d023ac33c2d9f8ec311ec`, not a second
independent cohort or replacement for the five-repeat timings:

- Default: [before](../benchmarks/external-recall/independent-2026-11-07/before-default.json), [after](../benchmarks/external-recall/independent-2026-11-07/after-default.json), [strict paired comparison](../benchmarks/external-recall/independent-2026-11-07/paired-default.json).
- Expanded: [before](../benchmarks/external-recall/independent-2026-11-07/before-expanded.json), [after](../benchmarks/external-recall/independent-2026-11-07/after-expanded.json), [strict paired comparison](../benchmarks/external-recall/independent-2026-11-07/paired-expanded.json).

All 18 case/profile pairs reproduced every before/after primary, excerpt and
map hit count. All nine corpus identities matched before/after. These native
receipts contain hashes and counts, not issue bodies, source packets or local
root paths. Their source fingerprints are on-disk observations, not loaded-code
attestation; root-location hashes alone do not establish corpus immutability.

Prerequisites: the exact local parquet and nine complete, license-checked
source snapshots listed in the manifest; Python 3.12; trusted before/after and
measurement checkouts outside the corpora. The exporter needs `pyarrow==22.0.0`
in an isolated environment. Collection and comparison use the standard library.
No dataset or archive is downloaded by these commands. Missing local snapshots
must be reported, never substituted; new large acquisition requires a shown
operation and approval, with no automatic cap increase.

Build only the nine already-exposed cases from the local pinned parquet:

```bash
export RECALL_DATASET=/abs/local/test-00000-of-00001.parquet
export RECALL_MANIFEST=/abs/measurement/benchmarks/external-recall/independent-2026-11-07/manifest.json
export RECALL_CASES=/abs/evaluation/cases.jsonl
python3.12 - <<'PY'
import ast, hashlib, json, os
from pathlib import Path
import pyarrow.parquet as pq
manifest = json.loads(Path(os.environ['RECALL_MANIFEST']).read_text())
dataset = Path(os.environ['RECALL_DATASET'])
assert dataset.stat().st_size == manifest['dataset']['bytes']
assert hashlib.sha256(dataset.read_bytes()).hexdigest() == manifest['dataset']['sha256']
selected = [c for c in manifest['cases'] if c['status'] == 'ready']
ids = [c['id'] for c in selected]
rows = pq.read_table(dataset, columns=['text_id', 'issue_title', 'issue_body', 'changed_files'],
                     filters=[('text_id', 'in', ids)]).to_pylist()
assert len(rows) == len(ids) == 9
by_id = {r['text_id']: r for r in rows}
cases = []
for entry in selected:
    row = by_id[entry['id']]
    case = dict(entry['case_metadata'])
    case['request'] = row['issue_title'] + '\n\n' + (row['issue_body'] or '')
    assert hashlib.sha256(case['request'].encode()).hexdigest() == entry['request_sha256']
    changed = ast.literal_eval(row['changed_files']) if isinstance(row['changed_files'], str) else row['changed_files']
    assert sorted(set(changed)) == case['changed_files']
    cases.append(case)
data = ''.join(json.dumps(c, sort_keys=True) + '\n' for c in cases).encode()
assert hashlib.sha256(data).hexdigest() == manifest['cases_sha256']
with Path(os.environ['RECALL_CASES']).open('xb') as output:
    output.write(data)
PY
```

Prepare the exact clean source roots named in `case_metadata.root`. Verify
compressed snapshot hashes before extraction; preserve symlinks without
following them. The manifest describes the link-aware corpus identity; verify
each recorded tree hash before and after collection. A checksum identifies
content, not an approval to execute repository code. Do not import, install,
test or run the inspected projects. Do not put receipts or extra metadata files
inside the inspected roots.

Run this identity check before **and** after collection, with the same manifest
and clean source roots. It hashes regular files and link targets as metadata;
it does not read through links or execute inspected code:

```bash
export RECALL_REPOS=/abs/evaluation/repos
python3.12 - <<'PY'
import hashlib, json, os
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
manifest = json.loads(Path(os.environ['RECALL_MANIFEST']).read_text())
repos = Path(os.environ['RECALL_REPOS']).resolve()
def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        while chunk := source.read(65536):
            result.update(chunk)
    return result.hexdigest()
def identity(root):
    assert root.is_dir() and not root.is_symlink()
    rows = []
    def walk(directory):
        with os.scandir(directory) as handle:
            entries = list(handle)
        for entry in entries:
            path = Path(entry.path)
            name = path.relative_to(root).as_posix()
            if entry.is_symlink():
                rows.append([name, 'symlink', os.readlink(path)])
            elif entry.is_dir(follow_symlinks=False):
                walk(path)
            elif entry.is_file(follow_symlinks=False):
                rows.append([name, entry.stat(follow_symlinks=False).st_size, sha(path)])
            else:
                raise ValueError('unsupported snapshot entry')
    walk(root)
    rows.sort(key=lambda row: PurePosixPath(row[0]))
    return hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()
for entry in manifest['cases']:
    if entry['status'] != 'ready':
        continue
    root = repos / entry['case_metadata']['root']
    assert identity(root) == entry['tree_sha256'], entry['id']
    license_path = root / Path(urlparse(entry['license_url']).path).name
    assert not license_path.is_symlink()
    assert sha(license_path) == entry['license_sha256'], entry['id']
print('Verified nine complete corpus identities and base-commit license files.')
PY
```

Then run the [shared-adapter recipe](../benchmarks/external-recall/README.md#reproducible-receipt-comparison)
at both complete budgets. Pin the two collector commits above and the
measurement checkout to `9361d028d836d561cd2d023ac33c2d9f8ec311ec`. Use the same
adapter for both arms and one unchanged case file/root directory. The default
flags are `--max-files 200 --max-entries 4000 --max-depth 8 --seconds 5
--excerpt-bytes 16384 --context-bytes 2048`; expanded uses
`--max-files 1000 --max-entries 10000 --max-depth 16 --seconds 30` with the
same byte limits. Keep outputs outside all source roots and do not overwrite
existing receipts. Compare each profile separately with the strict lexical
comparer. This reproduces file-level recall and single-call native timings;
it does not recreate the custom audit's tracing or five-repeat timing harness.

The preservation checks and custom harness remain in the separately retained
evaluation kit, identified by the hashes in the audit summary. The public
receipts/manifest support independent checking of the counts and an exact
native-adapter replay without distributing source corpora or task bodies.

## Decision and unverified claims

The frozen PR #30 retrieval change demonstrates limited independent file
recall gains with retained regressions. The exclusion can remove a supplied
relevant file. The filter ablation provides no delivered-recall reason to
remove it on these cases. Any ranking/query change motivated by this audit
should be developed separately, frozen before opening reserved task text or
results, and evaluated for losses as well as gains.

No model, host-answer grading, ChatGPT/Claude turn count, billed tokens,
cloud spending, whole-task success or owner-PC installation was measured or
qualified. Faster local preparation and higher file recall do not establish
those outcomes.
