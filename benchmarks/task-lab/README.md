# Task Lab: useful jobs with evidence and grading keys

Guidance refreshed November 11, 2026 for the reviewed dev38 code. See [current
build status](../../docs/current-status.md) for revision and verification scope,
[evaluation status](../../docs/evaluation-status.md) for retained real-model
results, and the [thinking-budget
comparison](../../docs/thinking-budget-2026-11-05.md) for separately declared
diagnostic caps. The normal replay below keeps the shipped baseline; no
larger-budget CLI option or model qualification is implied.

Ten synthetic, inert development cases are ready to replay. Each provides an exact task, source files, required evidence spans, critical findings and unsupported claims to watch for. This exposed set supports development; it is not a blind or independent evaluation.

| Job | Work delegated to the helper | Host still decides |
| --- | --- | --- |
| Repo tour | Trace a request through four files; identify placeholder components. | Whether the implementation meets the product goal. |
| Concurrency | Bring together the configured limit and contradictory admission condition. | The fix and its broader concurrency implications. |
| Change review | Compare count guards before/after without inventing regressions. | Whether the change is sufficient and safe to apply. |
| Failed-test triage | Link a synthetic failure log, assertion and condition. | The intended retry contract and required rerun. |
| Runtime mode | Separate a documented guarantee, default and environment-dependent branch. | What runtime evidence is still needed. |
| Boundary | Show the expression that contradicts inclusive-end documentation. | Which contract is intended. |
| Unknown hardware | Identify absent inventory/performance evidence. | Whether and how to obtain the missing measurements. |
| Source injection | Preserve the untrusted instruction and actual not-run status. | The supported answer, without obeying source text. |
| Distant contradiction | Retrieve two important regions far apart in one file. | Whether the declared rule matches implementation. |
| Coverage budget | Disclose incomplete search before a repository-wide judgment. | The next evidence request or scope limit. |

Run from the trusted project root on Linux with Python 3.11 or newer; substitute
an explicit supported interpreter if the default `python3` is older. This
diagnostic command executes no fixture code and calls no model:

```bash
PYTHONPATH=src python3 -B benchmarks/run_task_lab.py --evidence-only
```

Optional local-model replay, after that model is installed and the trusted daemon has cloud features disabled:

```bash
PYTHONPATH=src python3 -B benchmarks/run_task_lab.py \
  --model YOUR_INSTALLED_MODEL \
  --output /absolute/path/outside-fixtures/local-model-receipt.json
```

Replace `YOUR_INSTALLED_MODEL` with the exact permitted installed name.
`--case failure-triage` runs one case; repeat `--case` to select multiple IDs.
There is no automatic model download or cloud-provider call. A model replay
requests the current worker baseline (`junior_developer_handoff_v2`, 8,192 context tokens,
1,024 output tokens, thinking off, shared 30-second deadline); these requests
are not attested runtime settings, a tuned profile or automatic qualification.
A model whose declared thinking controls cannot be switched off is refused
before source is sent and the receipt records the error for every case.
Current deadlines may reject a cold or reasoning-heavy model; retain that
failure rather than silently widening budgets or retrying.

`--dataset /absolute/dataset` selects a dataset following the [external
contract](../../docs/held-out-evaluation.md); the bundled lab remains
development material even when selected explicitly. A supplied `--output` must
be a new file outside the entire dataset, not merely outside its fixture
subdirectories. The script never overwrites an earlier receipt. The optional
`--rerank-model` explicitly calls an installed loopback embedding model; the
plain evidence-only command above does not. The experimental `--datamark`
requires `--model` and marks only the worker's copy of source, not exact
evidence or fixture files. These options add no promotion decision.

`manifest.json` contains model-facing tasks. `grading-keys.json` stays outside every fixture root and is never sent to the worker by the runner. Do not point the helper at the whole benchmark directory when measuring answer quality. Source fixtures are inert; their imports, network strings and hostile comments are not executed.

The receipt checks required spans, excerpt hashes, scan-limit disclosure and unchanged fixtures. Semantic review fields stay PENDING/null. A zero exit status means these mechanical checks passed and no recorded worker error occurred; it does not mean the model's statements were true. A reviewer must separately grade critical misses, unsupported claims and useful abstention.

The first diagnostic found that one-window-per-file retrieval missed the
distant executable condition. Current primary selection considers up to two
windows per matching file, preferring one window per distinct file within a
**four-primary-window** budget. The controlling-context pass may then add up to
four definition windows, one usage window and one test window: **ten evidence
records at most**, not four total. Context has its own byte cap within the
shared excerpt budget; neither pass guarantees complete source coverage.
Omitted matching regions disclose `window_budget`, while context omissions
have separate cutoffs.

Current default walk limits are 1,000 files, 20,000 directory entries, depth
eight and five seconds, with 16,384 excerpt bytes and 2,048 context bytes.
Individual manifest cases can declare different validated limits. The time
limit bounds the walk, not all scoring/context/rerank work afterward.

The [November 11 source-span
diagnostic](../../docs/source-span-development-2026-11-11.md) uses a separate
six-case generated development dataset and independent exact-byte readback.
Its pinned dev32/dev35 comparison counts 11/18 versus 17/18 required spans and
retains an oversized-anchor miss (3/6 versus 5/6 mechanical case passes).
Those commands intentionally exit 1 while preserving complete receipts; that
known miss must not be removed from the denominator. These cases and the ten
bundled cases are exposed development material, not new unseen evaluation.

Tiny fixtures cannot establish token savings. The end-to-end study also needs realistic large inputs, a trivial-task bypass baseline, cold/warm runs, source-change recovery and an unseen test set.

For checkpointed repeated runs, frozen identities and a receipt-bound grading sheet, use [the PC trial guide](../../docs/pc-readiness-and-trials.md). The simpler replay above remains a mechanical diagnostic.
