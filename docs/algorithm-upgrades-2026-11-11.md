# Anchored source coverage and stable embedding scores

November 11, 2026 · development candidate `0.4.0.dev34`, based on main `9a834ed`.

This change improves deterministic source-window coverage and numerical reliability without adding runtime dependencies. The original checkout and running preview are preserved. Real-model accuracy, general retrieval quality and whole-task savings remain unqualified.

## A rejected intermediate candidate

The initial dev33 candidate at `ba9d56f` maximized weighted line coverage across two windows before the global four-primary-record cap. Its per-file optimum and 492 tests passed, but a subsequent cross-file probe found the wrong product behavior: two dense clusters of audit comments displaced an earlier `cancel_task` guard. Three other matching files consumed the remaining primary slots, so only the first dense window was excerpted. The baseline had included the guard. A line-index entry was available, but that did not preserve its full source context.

This is a development regression, not evidence that the guard was semantically understood. The unconstrained pair-first objective is rejected before merge. Dev34 preserves the strongest original matching-line anchor as the primary window, then optimizes additional coverage. The new regression failed against dev33 with context enabled and disabled and passes after this correction. Snapshot/source identities change with the implementation; prior evidence does not qualify this revision automatically.

## Synthetic observations

The pre-upgrade main baseline passed 481 Python tests. Controlled probes produced these results:

| Probe | Main baseline | Final candidate |
| --- | --- | --- |
| Two matching lines four lines apart | Ranges 1–4 and 2–8 repeated three lines; 99 excerpt bytes | Ranges 1–4 and 5–8 repeat no lines; 72 bytes for the same source-line union |
| Same overlap case with a 72-byte cap | Second match omitted | Both matches captured within the cap |
| Seven hits: two isolated early lines and five clustered later lines | Two matches captured | Six matches captured, with the remaining hit disclosed in the line index |
| Four matching files, cancellation guard before repeated audit comments | Guard excerpted | Guard excerpted; dev33 had lost it |
| Collinear / orthogonal vectors scaled by 1e300 | NaN / NaN | Approximately 1 / 0 |
| Same vectors scaled by 1e-300 | Nonzero vectors refused as zero | Approximately 1 / 0 |
| Embedding coordinate `10**1000` | Unhandled `OverflowError` | Explicit numeric refusal and exact lexical fallback |

These constructed examples are development evidence, not estimates of user-task success. The four-primary-record cap, bounded controlling context and explicit cutoff records remain in effect. ACC-01, ACC-02 and MET-01 remain open.

## Maximum additional coverage with a fixed anchor

File-level BM25-style ranking is unchanged. For each matching file, the existing inverse document frequency of query term t is:

`idf(t) = log(1 + (N - df(t) + 0.5) / (df(t) + 0.5))`.

Matching line i has weight `w(i) = sum(idf(t) for matched terms t on line i)`. Every matching line proposes a centered window of at most seven lines, as before. Fix A to the window centered on the highest-weight matching line, choosing the earliest line on ties. This preserves the original first-window rule and its priority when several files compete for slots.

Compare every candidate B to maximize:

`gain(B | A) = sum(w(i) for matching lines i in B but not A)`.

If no candidate adds a matching line, emit A alone. Otherwise choose the largest gain, break ties by anchor weight and earlier position, and trim overlap from B. Centered windows have monotone starts and ends, so any added source lies on at most one edge of A. Trimming leaves the union intact and each exact source line appears once. Selection takes O(m) time and space for m matching lines because candidate width and window count are fixed.

The optimum is conditional on A, not an unconstrained best pair. It precedes global record and byte limits; it does not maximize semantic relevance, distinct terms, repository coverage or useful evidence per byte. Repeated matching terms can still outweigh a rare second-region match, and an oversized window can still be omitted by the byte cap. Separate context, map and line-index limits still apply. Path-only matches retain the previous first-four-line fallback. No text is summarized or rewritten by selection.

The relevance-versus-novelty motivation appears in Carbonell and Goldstein's [original MMR paper](https://www.cs.cmu.edu/afs/cs/Web/People/jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf). This implementation uses explicit anchored line coverage, not MMR or a learned relevance model. An initial SciSpace search also surfaced [Probabilistic latent maximal marginal relevance](https://scispace.com/papers/probabilistic-latent-maximal-marginal-relevance-2w9x3rvkcc); its abstract informed comparison, not an implementation or performance claim.

## Scale-invariant cosine scoring

For each finite nonzero vector v, compute:

- `s = max(abs(v_i))`
- `z_i = v_i / s`
- `u_i = z_i / hypot(*z)`
- `cosine(q, v) = fsum(u_q_i * u_v_i)`

Scaling cancels algebraically. At least one scaled coordinate has magnitude one; its norm is between one and the square root of the dimension count. This avoids overflow and underflow from squaring extreme finite coordinates. Clamp the final result to [-1, 1] for floating-point roundoff. Python documents norm and compensated summation in its [math reference](https://docs.python.org/3.12/library/math.html).

Zero vectors, nonfinite values, booleans, strings, invalid dimensions and integers outside the finite float range are explicit refusals. Refusal retains the exact lexical packet and current invocation's attempt receipt. Model identity, loopback restrictions, truncation disclosures, transport limits and opt-in model policy are unchanged. Synthetic replies were used; no real model received source.

## Validation plan and results

| Area | Check | Target / result |
| --- | --- | --- |
| Core and integration contracts | Full unittest suite | 493 tests pass on Python 3.12 and 3.14 |
| Strongest-anchor preservation | Four-file synthetic source collection, context on/off | Guard and all four file primaries retained with exact hashes |
| Conditional coverage optimum | Independent brute-force oracle on 202 deterministic layouts | Same optimum with original anchor fixed; no overlap and at most two seven-line windows |
| Evidence integrity and budgets | Unicode/CRLF bytes, hashes, cutoff/index and repeat checks | Exact text retained; overlap budget regression passes |
| Numeric reliability | Independent positive scaling, subnormal/largest finite floats, cancellation, malformed replies | Finite cosine values or explicit refusal with exact fallback |
| Existing exposed development tasks | Retrieval smoke and evidence-only Task Lab | 2/2 sources and 10/10 mechanical cases; not unseen qualification |
| Distribution and adapter | Clean wheel, isolated installed tests, demo/shared and official SDK smoke | All 493 installed tests and all smoke checks pass |

The final dev34 wheel was built with setuptools 84.2.1 and wheel 0.48.0. Code, assets and legal notices matched source bytes; core runtime dependencies remain empty. All 493 tests passed with PYTHONPATH unset in a new installed environment. Packaged-demo/shared-coordinator checks preserved exact evidence and retained Local AI off after restart. Official SDK 2.3.0, installed from hash-locked requirements, passed stdio subprocess, shared-service and in-process checks with no model/cloud calls.

The oracle changed because the product requirement changed: the anchor is now a constraint. It independently enumerates every possible second window, rather than replaying the implementation's loop. No claim of an unconstrained pair optimum remains.

The earlier dev33 261,000-byte/29,000-hit stress probe took 0.312 seconds on this machine and belongs to the rejected algorithm. The same generated input completed in 0.065 seconds with dev34, selecting two records and 99 bytes with explicit window/index cutoffs. These are single observations, not a comparative performance study. Final tests do not qualify representative throughput, memory, actual embedding quality, host answers or total task time.

No browser UI or adapter contract changed, and this pass does not update the live preview. Build environments, logs and wheels remain local temporary artifacts. Browser/device, owner-PC, human review and independent security gates are separate.

## Remaining work

Expand fresh cross-file development comparisons with separately reviewed required evidence and retain losses alongside wins before any semantic-quality claim. Complete the private-data handoff policy and durable recovery work in TODO.md. Reserve new qualification cases only after development gates pass and exact source/settings/model identities are frozen.
