# Local Ollama routing

The local worker is optional. The core, GUI and default MCP tools still prepare exact evidence without it. No model is downloaded, daemon started, cloud provider called, or inspected source executed by this integration.

## Owner configuration

Keep configuration and profile policies outside inspected roots. Extend the normal TOML configuration with:

```toml
[ollama]
enabled = true
port = 11434
```

The host is fixed to `127.0.0.1`. HTTP uses no proxy environment variables and follows no redirect. For private source, use a trusted local daemon with cloud features disabled, as described in the [official local-only guidance](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features). Model metadata checks cannot attest a daemon's upstream network policy or loaded weight bytes.

## Three modes

| Mode | Behavior |
| --- | --- |
| `off` | Deterministic evidence only; no Ollama inventory or generation request. |
| `best` | Requires an owner-controlled reviewed, held-out profile for this task, installation, pipeline, settings and runtime. No eligible profile makes no Ollama request. |
| `trial` | Explicit installed model and complete digest; unqualified candidate notes remain labeled as interpretations. No task-accuracy claim. |

List the actual installed inventory, then pin a model/digest for a deliberate trial:

```bash
shake-bake models --config /path/to/config.toml
shake-bake prepare --config /path/to/config.toml --project my_project \
  --request 'Prepare the exact startup evidence.' --task-kind troubleshoot \
  --local-ai trial --model EXACT_INSTALLED_TAG --digest FULL_SHA256
```

Omit `--select` for bounded lexical discovery, or retain exact ranges. The original request and every collected source record remain unchanged in the handoff. No model can choose additional roots, remove source, expand permissions or declare the task solved.

## Model and response checks

Before source submission, `/api/tags` must match the pinned digest and `/api/show` must report local GGUF completion metadata and sufficient context. Known cloud names/remote descriptors are excluded. Runtime version and model digest are checked again after inference; a mismatch discards the note. The [official chat API](https://docs.ollama.com/api/chat) and [structured output contract](https://docs.ollama.com/capabilities/structured-outputs) informed this implementation.

A worker exchange has a 30-second cooperative deadline with a socket-shutdown watchdog, 16 KiB serialized input cap, 256 KiB response cap, requested 8,192-token context, at most 512 output tokens, temperature 0 and no retry. Byte limits do not prove tokenizer/template fit. Metadata and inference share the exchange deadline. Reported token usage beyond the profile budget is refused.

Thinking-capable models receive `think: false`. Newer explicit metadata must permit false. Older daemons may omit the metadata; their returned message must still contain no thinking output. Tool calls, unknown evidence IDs, duplicate JSON keys/citations, malformed notes, changed model identity and incomplete/length-limited completions are refused. Schema/citation validity is not semantic accuracy.

Any failed worker attempt keeps the exact evidence and a visible abstention reason, with no replacement model/provider attempt. An unavailable selected qualified profile also abstains rather than silently choosing a lower-ranked replacement. Cancellation discards a whole job; the local-AI pause stops this client's model wait while keeping checked source available. Closing a connection does not prove the daemon stopped GPU work.

## Qualification records

No qualified profile ships. For automatic routing, add `profile_policy = "/path/outside/projects/profiles.json"` at the top level of the TOML configuration. The JSON policy must be an owner-owned regular file, not writable by group/others, with no symlink ancestors. It has `schema_version: 1` and a `profiles` array (up to sixteen).

Each profile has `id`, `model`, `digest`, `tasks`, `enabled` and `qualification`. A candidate has `qualification: null`. A qualifying record requires `reviewed`, `held_out`, `dataset`, `dataset_version`, `unique_cases` (at least 20), `accuracy`, `baseline_accuracy`, `critical_misses` (0), `unsupported_critical_claims` (0), `median_seconds`, `device_id`, `pipeline_sha256`, `runtime_version` and exact `options`. Obtain the current installation/pipeline identity with `shake-bake profile-info --config …`. Current options are `temperature: 0`, `num_ctx: 8192`, `num_predict: 512`, `seed: 0`.

Comparable records must share the cohort/version, unique case count and native-host baseline. Recorded accuracy must meet that baseline. Highest accuracy wins; lower latency breaks accuracy ties. Identity/settings changes invalidate the record. The installation ID persists in the private store; it is not hardware attestation. Actual GPU/runtime/hardware calibration remains a separate gate.

Owner records are declarations, not authenticated certificates or proof a trial stayed unseen. Test qualifications are fabricated synthetic fixtures. No actual task/model pair is qualified by this release, and no savings has been measured.
