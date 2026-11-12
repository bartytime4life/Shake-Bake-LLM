# Recorded-accuracy routing, explanations and the off switch

Reviewed November 11, 2026 against the documented dev37 source candidate. The policy engine first appeared in the historical 0.3.0.dev3 candidate. It now serves the `assist` CLI and the shared workbench/stdio preparation session; only explicit standalone diagnostics use a separate fixed-model or evidence-only launch. See [current source and delivery status](current-status.md) and [shared coordination](shared-coordinator.md).

No learned task classifier, automatic qualification or real-model winner is supplied. The failed-run source-location workflow uses deterministic parsing and source reads, without this model-selection path. A source brief can be evidence-only, use an eligible owner-recorded profile, or run an explicitly allowed/acknowledged pinned candidate trial. A candidate trial is not qualification and cannot promote a profile.

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

An owner policy can also set `enabled=false` globally or mark an individual profile `disabled`. In the normal GUI, the shared Local AI off choice is persisted privately and new installs start paused; switching off also cancels the service's owned active preparation runner. A direct CLI flag affects that invocation. Neither action kills an already-running Ollama daemon or proves GPU inference cancellation. Explicit standalone diagnostics have their own session. See [Local AI preference boundaries](local-ai-preferences.md).

## What a profile must record

Policy baselines are per task family: code, troubleshoot, documents or search. Each declares a dataset ID/version, native-host baseline ID, common case count and reviewed final-task accuracy. A profile records its model tag, full expected digest, preparation-pipeline fingerprint and an evaluation record for that same cohort.

The selector requires a qualified status, reviewed held-out evaluation, matching dataset/baseline/case count, zero recorded critical misses, zero recorded unsupported critical claims and accuracy at least as high as the paired native baseline. Development-only or unreviewed records do not pass. Profiles whose model identity or pipeline changed are excluded. Eligible profiles are ordered by recorded accuracy, then latency for accuracy ties, then ID for deterministic output.

The `Why this model` explanation states the selected model, task, recorded result, baseline and tie-breaking rule. Rejection codes distinguish absent qualification, owner disabling, critical failures, incomparable trials, stale identity and unavailable models. A failed attempt retains its profile/model identity and reason, discards the note and returns the source. No weaker fallback or automatic retry is attempted.

The pipeline fingerprint hashes the selected Python source modules for package version, contracts, collection/search, worker/briefing/routing, helper/runner/protocol, GUI/shared/MCP, readiness/preferences, and failed-run parsing/screening/service. This is a source identity, not attestation of browser assets, loaded model weights, external SDK, runtime or hardware. Relevant changes invalidate a profile's matching pipeline record. Owner policies must live outside the inspected root; repository source and worker text cannot supply qualification records through this interface. Policies are bounded JSON with duplicate/nonfinite values refused.

**These are owner-controlled review records, not authenticated test certificates.** The implementation checks consistency and gates behavior; it cannot establish that a reviewer ran the claimed trial, that a dataset stayed unseen, or that the scores are statistically decisive. The finite held-out trial also does not guarantee future answers. The owner must protect and independently review qualification records. No real profile has been qualified in this build.

## Observed local model identity

The routed path checks eligible records before contacting the daemon; a missing eligible profile or missing usable evidence means evidence-only fallback. When a model is selected, loopback `GET /api/tags` must match its expected digest before source submission and after the response. `/api/show` metadata is checked before source is sent, including refusal when explicit thinking controls cannot disable thinking. Observed runtime and requested settings are recorded; a changed runtime during the call withholds the note. Inventory/generation use bounded, no-proxy/no-redirect transport. Metadata requests contain no source packet.

An inventory mismatch before source submission blocks the model call. A mismatch after inference discards the note and preserves evidence. The returned worker note records the matching reported digest. These checks observe a trusted daemon's tag metadata: they do not attest loaded weight bytes or prevent every concurrent tag-change race. Ollama/runtime/driver changes and other environmental changes still require owner review; the router does not automatically fingerprint the whole machine.

The additional inventory calls and cold loading belong in full-task timing/usage measurements. They are a correctness check to evaluate, not a savings result. Implementation HTTP tests use simulated services; the [evaluation record](evaluation-status.md) separately retains real local development runs, rejected prompts and limited host diagnostics. Those runs do not qualify a shipped profile, prove representative model/host quality, or establish whole-task savings. [Current validation](current-status.md) keeps program, installed, browser, SDK, host and owner-installation evidence separate.

Reference: [Ollama local inventory API](https://docs.ollama.com/api/tags).
