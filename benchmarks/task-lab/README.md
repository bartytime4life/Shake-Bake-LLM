# Task Lab: useful jobs with evidence and grading keys

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

Run the diagnostic path on Linux, without executing fixture code or calling a model:

```bash
PYTHONPATH=src python3 -B benchmarks/run_task_lab.py --evidence-only
```

Optional local-model replay, after that model is installed and the trusted daemon has cloud features disabled:

```bash
PYTHONPATH=src python3 -B benchmarks/run_task_lab.py \
  --model qwen3.5:9b-q4_K_M \
  --output /absolute/path/outside-fixtures/local-model-receipt.json
```

`--case failure-triage` runs one case. There is no automatic model download or cloud-provider call. A model replay requests the current worker baseline; it is not a tuned profile or automatic model qualification. Current deadlines may reject a cold or reasoning-heavy model; retain that failure rather than silently widening budgets or retrying.

`manifest.json` contains model-facing tasks. `grading-keys.json` stays outside every fixture root and is never sent to the worker by the runner. Do not point the helper at the whole benchmark directory when measuring answer quality. Source fixtures are inert; their imports, network strings and hostile comments are not executed.

The receipt checks required spans, excerpt hashes, scan-limit disclosure and unchanged fixtures. Semantic review fields stay PENDING/null. A zero exit status means these mechanical checks passed and no recorded worker error occurred; it does not mean the model's statements were true. A reviewer must separately grade critical misses, unsupported claims and useful abstention.

The first diagnostic found that one-window-per-file retrieval missed the distant executable condition. The revised collector permits two ranked windows per file while preferring one window per distinct file within the existing four-record budget. Omitted matching regions get a `window_budget` flag. All ten development cases now retain their required spans; this does not establish completeness on unseen repositories.

Tiny fixtures cannot establish token savings. The end-to-end study also needs realistic large inputs, a trivial-task bypass baseline, cold/warm runs, source-change recovery and an unseen test set.

For checkpointed repeated runs, frozen identities and a receipt-bound grading sheet, use [the PC trial guide](../../docs/pc-readiness-and-trials.md). The simpler replay above remains a mechanical diagnostic.
