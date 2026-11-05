# Recovered planning record

The implementation brief is [Shake and Bake LLM Assistant — Local Work Engine and Cloud Escalation Plan](https://docs.google.com/document/d/1llXN3-oNzIWi7DL1yU3KwXK_tE-RaBqrXRjPwE5Y-3s/edit), modified November 4, 2026 (America/Chicago), retrieved November 4, 2026.

The source describes a standalone Python application that prepares exact local evidence for Claude and ChatGPT. Its priorities are correctness, source coverage, explicit uncertainty, local execution for mechanical operations, and measured cloud assistance. Ollama is optional. No external business application is a required dependency.

The plan reports a separate `0.4.0.dev4` prototype, 121 passing program tests, a local GUI and a shared coordinator. Those are historical claims about a source package linked from ChatGPT Library. They are **not validation results for this checkout**. The repository was empty when this work began. The original package must be recovered and reconciled before claiming parity with it.

The full planning export is retained locally in `.local/recovered/` and excluded from Git. This repository contains only the implementation decisions needed to develop and review the software.

## Accepted direction

- Preserve the original request and exact source excerpts, line ranges and source hashes.
- Enforce explicit project roots and read-only, bounded collection in application code.
- Treat inspected source, logs and model output as untrusted data.
- Use deterministic software before adding a model call.
- Keep one coordinator responsible for jobs, evidence and cancellation.
- Return a compact handoff with gaps and retrieval handles; make no diagnosis or token-savings claim from collection alone.
- Keep cloud calls, model downloads, repository execution and writes outside the first local-core slice.

## Qualification still required

Actual Ollama/model performance, native host interoperability, the owner's hardware, Windows filesystem boundaries, independent security review, unseen correctness trials and whole-task savings require their own evidence. Program tests do not qualify these properties.
