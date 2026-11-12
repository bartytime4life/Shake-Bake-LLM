# Native retrieval and deterministic preparation development cases

This reproduces the dated comparison's synthetic inputs. [Current source and validation](../../docs/current-status.md) are separate; generating the fixtures does not rerun that comparison or create new host/accuracy evidence.

These four AI-authored synthetic projects test a targeted-search baseline against
the same host and tools with an optional brief from the unchanged application.
They are exposed development material, not an unseen qualification cohort.

Generate a new directory outside the checkout:

```bash
python3.12 -B benchmarks/native-preparation/generate.py /absolute/new/dataset
```

The command refuses an existing destination. It writes one `fixtures/<case>`
project per task, a byte/line/hash manifest, and separate grading keys. Give a
host read access to only its single fixture directory. Neither the generator nor
the manifest or grading keys belongs inside that readable root. The generator
contains the expected findings and is evaluator material.

| Case | Files | Source bytes | Task |
| --- | ---: | ---: | --- |
| `dispatch-path` | 78 | 281,339 | Trace configuration and routing; distinguish a request description from actual traffic. |
| `publish-reorder` | 79 | 281,704 | Review a pinned reorder against its shared contract and existing test. |
| `two-log-failures` | 78 | 363,140 | Recover two distinct failures from a repetitive synthetic log. |
| `deployment-unknowns` | 78 | 281,156 | Separate configuration, candidate tags, missing measurements and untrusted instructions. |

Each project includes 72 unrelated synthetic utility files. This adds search
volume, not realistic application complexity. Source and logs remain inert; no
fixture code or tests are executed. Exact generated file identities and all
results must be retained. Do not revise fixtures or the helper after inspecting
results and relabel the same cases as unseen.

See the [comparison record](../../docs/native-preparation-2026-11-05.md) for the
frozen method, measurements and limitations. No live cloud run belongs in CI.
