# Recorded-accuracy routing, explanations and the off switch

Development candidate 0.3.0.dev3 implements a routing policy engine and the `assist` CLI. No GUI, automated quality certification, learned task classifier, routing MCP tool or real-model winner is supplied. The current MCP adapter still uses its explicit fixed-model launch configuration.

## Try the safe shipped policy

```bash
PYTHONPATH=src python3 -B -m shake_bake assist \
  --root examples/review-fixture \
  --task-kind code \
  --task "Find executable slice coverage." \
  --policy examples/routing-policy.json
```

This example intentionally selects no model: all shipped profiles are candidates, with no qualification, digest or invented scores. It returns exact evidence, `ABSTAIN` and an explanation that no profile qualifies. Exit 3 means there is no model-prepared handoff. JSON output also explicitly requires host reasoning and sets final-answer readiness false.

The off switch bypasses all inventory and generation calls, while preserving source collection:

```bash
PYTHONPATH=src python3 -B -m shake_bake assist \
  --root examples/review-fixture \
  --task-kind code \
  --task "Find executable slice coverage." \
  --disable-local-ai
```

An owner policy can also set `enabled=false` globally or mark an individual profile `disabled`. These switches affect new invocations. They do not kill an already-running Ollama daemon or prove GPU inference cancellation. Existing task-session cancellation remains a separate operation.

## What a profile must record

Policy baselines are per task family: code, troubleshoot, documents or search. Each declares a dataset ID/version, native-host baseline ID, common case count and reviewed final-task accuracy. A profile records its model tag, full expected digest, preparation-pipeline fingerprint and an evaluation record for that same cohort.

The selector requires a qualified status, reviewed held-out evaluation, matching dataset/baseline/case count, zero recorded critical misses, zero recorded unsupported critical claims and accuracy at least as high as the paired native baseline. Development-only or unreviewed records do not pass. Profiles whose model identity or pipeline changed are excluded. Eligible profiles are ordered by recorded accuracy, then latency for accuracy ties, then ID for deterministic output.

The `Why this model` explanation states the selected model, task, recorded result, baseline and tie-breaking rule. Rejection codes distinguish absent qualification, owner disabling, critical failures, incomparable trials, stale identity and unavailable models. A failed attempt retains its profile/model identity and reason, discards the note and returns the source. No weaker fallback or automatic retry is attempted.

The pipeline fingerprint covers the relevant package version, contracts, collector, search, worker, briefing and routing source. Owner policies must live outside the inspected root; repository source and worker text cannot supply qualification records through this interface. Policies are bounded JSON with duplicate/nonfinite values refused.

**These are owner-controlled review records, not authenticated test certificates.** The implementation checks consistency and gates behavior; it cannot establish that a reviewer ran the claimed trial, that a dataset stayed unseen, or that the scores are statistically decisive. The finite held-out trial also does not guarantee future answers. The owner must protect and independently review qualification records. No real profile has been qualified in this build.

## Observed local model identity

The routed path uses the documented loopback `GET /api/tags` inventory. The selected expected digest must match inventory before source submission and after the model response. Existing `/api/show` local-metadata checks still run before source is sent. Inventory and generation use the existing bounded, no-proxy/no-redirect transport. Metadata requests contain no source packet.

An inventory mismatch before source submission blocks the model call. A mismatch after inference discards the note and preserves evidence. The returned worker note records the matching reported digest. These checks observe a trusted daemon's tag metadata: they do not attest loaded weight bytes or prevent every concurrent tag-change race. Ollama/runtime/driver changes and other environmental changes still require owner review; the router does not automatically fingerprint the whole machine.

The additional inventory calls and cold loading belong in full-task timing and usage measurements. They are a correctness check to evaluate, not a savings result. Successful HTTP tests here use a simulated local service. Real Ollama and host-integration qualification remain pending.

Reference: [Ollama local inventory API](https://docs.ollama.com/api/tags).
