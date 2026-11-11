# Weighted source coverage and stable embedding scores

November 11, 2026 · development candidate `0.4.0.dev33`, based on main `9a834ed`.

This change improves deterministic source-window coverage and numerical reliability. It adds no runtime dependencies. The original checkout and running preview are preserved; this candidate is developed in an isolated worktree. Real-model accuracy, general retrieval quality and whole-task savings remain unqualified.

## Evidence and priorities

The baseline passed 481 Python tests on Python 3.12. Synthetic probes nevertheless reproduced two defects:

| Probe | Before | After |
| --- | --- | --- |
| Two matching lines four lines apart | Ranges 1–4 and 2–8 repeated three lines; 99 excerpt bytes | Ranges 1–4 and 5–8 repeat no lines; 72 bytes for the same source-line union |
| Same overlap case with a 72-byte cap | Second match omitted | Both matches captured within the cap |
| Seven matching lines: two isolated early hits and five clustered later hits | Two matches captured | Six matches captured, with the remaining hit disclosed in the line index |
| Collinear / orthogonal vectors scaled by 1e300 | NaN / NaN | Approximately 1 / 0 |
| Same vectors scaled by 1e-300 | Nonzero vectors refused as zero | Approximately 1 / 0 |
| Embedding coordinate `10**1000` | Unhandled `OverflowError` | Explicit numeric refusal and exact lexical fallback |

These are deliberately constructed development examples, not estimates of user-task success. The application still chooses at most four primary records across files and may append bounded controlling context. Neither fix closes ACC-01, ACC-02 or MET-01.

## Maximum weighted line coverage

The file-level BM25-style ranking remains unchanged. For each matching file, let the existing inverse document frequency of query term t be:

`idf(t) = log(1 + (N - df(t) + 0.5) / (df(t) + 0.5))`.

A matching line i has weight `w(i) = sum(idf(t) for matched terms t on line i)`. Every matching line proposes the same centered window of up to seven lines as before. Choose at most two such windows to maximize:

`F(S) = sum(w(i) for distinct matching lines i covered by S)`.

The new sweep finds the maximum for that finite candidate set before applying global record and byte budgets. It does not claim to maximize semantic relevance, distinct query terms, repository coverage or useful evidence per byte.

The centered intervals have monotonically increasing starts and ends. For each right interval:

1. The best disjoint left partner is the highest-weight interval in the completed prefix.
2. Among overlapping partners, the earliest start covers a superset of any later partner when united with the right interval. Weights are nonnegative, so checking that partner suffices.
3. Compare these pairs with the single interval and keep the best coverage.

Sorting costs O(m log m) and the sweep O(m), with O(m) auxiliary storage for m matching lines. Each candidate has at most seven lines. The stronger individual window is emitted first; equal choices are deterministic. Overlap is trimmed from the second interval, preserving the selected union and exact source bytes. Path-only matches retain the previous first-four-line fallback. Separate primary-window, context, excerpt, map and line-index limits still apply, with existing cutoff records.

This is a line-coverage objective; repeated matching terms on different lines can outweigh one rare match. A globally selected record may still be omitted if it exceeds the byte budget. Changing selected spans changes snapshot IDs through the existing exact span/hash binding; no prior model qualification transfers automatically.

The broader relevance-versus-novelty motivation is described in Carbonell and Goldstein's [original MMR paper](https://www.cs.cmu.edu/afs/cs/Web/People/jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf). This implementation uses an explicit interval-coverage objective, not MMR or a learned relevance model. A SciSpace search also surfaced [Probabilistic latent maximal marginal relevance](https://scispace.com/papers/probabilistic-latent-maximal-marginal-relevance-2w9x3rvkcc); its abstract informed the research comparison, not an implementation or performance claim.

## Scale-invariant cosine scoring

For each finite nonzero vector v, compute:

- `s = max(abs(v_i))`
- `z_i = v_i / s`
- `u_i = z_i / hypot(*z)`
- `cosine(q, v) = fsum(u_q_i * u_v_i)`

Scaling cancels algebraically. At least one scaled coordinate has magnitude one; the scaled norm is between one and the square root of the dimension count. This avoids overflow from squaring large finite values and underflow from squaring very small values. The final result is clamped to [-1, 1] for floating-point roundoff. Python documents the norm and compensated summation operations in the [math reference](https://docs.python.org/3.12/library/math.html).

Zero vectors, nonfinite values, booleans, strings, invalid dimensions and integers outside the finite float range remain explicit refusals. Refusal retains the exact lexical packet and records the current invocation's attempts. Model identity, loopback restrictions, truncation disclosures, transport limits and the opt-in model policy are unchanged. Synthetic reply stubs were used; no real model received source during this work.

## Validation

- Baseline: 481 Python 3.12 tests passed.
- Candidate: 492 tests passed on Python 3.12 and 3.14, including 11 new regressions. The new failure cases were run against the baseline first.
- Coverage oracle: all 202 deterministic synthetic layouts match exhaustive enumeration of the best one/two-window union, including unequal term weights. Regressions also check exact Unicode/CRLF bytes and hashes, non-overlap, deterministic output, caps and remaining-hit disclosure.
- Numeric checks cover independent positive query/candidate scaling, the smallest subnormal and largest finite float, orthogonal/opposite vectors, cancellation, integer coordinates, malformed replies and exact fallback.
- Existing retrieval smoke: 2/2 expected sources found. Bundled evidence-only Task Lab: 10/10 mechanical passes with original fixtures and hashes intact. These exposed cases are not unseen evaluation.
- A single generated 261,000-byte file with 29,000 matching lines completed source preparation in 0.312 seconds on this development machine. It returned two records, 126 excerpt bytes and explicit window/index cutoffs. This one observation is not a throughput or resource-bound qualification.

- A clean dev33 wheel was built with setuptools 84.2.1 and wheel 0.48.0. Wheel code/assets/legal notices matched source bytes; core runtime dependencies remain empty. All 492 tests passed from an isolated installed environment with PYTHONPATH unset.
- Installed packaged-demo/shared-coordinator smoke passed, including exact evidence and retained Local AI off after restart, using disposable state.
- Official SDK 2.3.0 was installed from the hash-locked requirements. Its stdio subprocess, shared-service and direct-adapter smoke checks passed with synthetic data and no actual model/cloud calls.

No browser UI or adapter contract changed, and no browser suite or live preview was updated during this pass. Owner-PC, human review, independent security, actual embedding quality and paired final-host outcomes remain separate gates. Test logs, build environments and wheels are local temporary artifacts outside the committed source.

## Follow-up priorities

1. Compare the changed selection on fresh cross-file development cases with separately reviewed required evidence; record losses as well as wins before proposing any semantic-quality claim.
2. Complete the existing private-data handoff policy and durable recovery work in TODO.md. The algorithm changes do not substitute for them.
3. Freeze exact source/settings/model identities only after development gates pass, then reserve new cases and obtain separate human review before any qualification or promotion.
