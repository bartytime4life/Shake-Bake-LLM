# Saved Local AI choice and external evaluation inputs — November 5, 2026

This development candidate follows main `7092a63` (`0.4.0.dev6`). It fixes restart behavior and adds the missing private-dataset input mechanism. It does not qualify a model or actual Claude/ChatGPT host.

## Changes

- The normal GUI stores only the Local AI on/off choice in private local state. A new installation starts paused; explicit on/off survives restart. Single-writer locking, private file/directory permissions, atomic replacement and explicit storage failures are implemented. Unsafe/corrupt settings do not silently start enabled. See [settings boundaries](local-ai-preferences.md).
- Starting a task no longer changes the global AI setting. A stale browser cannot resume a service that another control paused. The interface distinguishes persistent settings from session-only diagnostic settings. Jobs and captured evidence still do not survive restart.
- The source launcher finds an installed Python 3.11+ without downloading one. The review machine's default `python3` is 3.10.9; the launcher selected the supported installed interpreter and completed an actual local HTTP restart check using temporary private settings.
- Trial tools accept an explicit external dataset, record owner-declared split/identity, keep grading keys outside preparation inputs, reject unsafe case paths/links/limits, pin input hashes and stop on drift. A final-attempt grading change is retained as a failed/stopped attempt. The bundled lab remains development data. See [external evaluation inputs](held-out-evaluation.md).
- Current entry-point documentation reconciles earlier 121/140-test and untouched-model/SDK wording with the scoped `.dev5`/`.dev6` evidence. Historical receipts are unchanged. Model/pipeline fingerprints change with this candidate and invalidate earlier matching policies.

## Executed checks

- Baseline: 140 tests passed on Python 3.14 before edits. Candidate: 156 source tests pass on Python 3.14; the 16 new tests cover saved settings/restart/failure boundaries and temporary external synthetic datasets. All model calls in these tests use a simulated loopback service.
- A clean `0.4.0.dev7` wheel passes the exact packaged source/web/demo/legal-file verifier, with no required runtime dependencies. All 156 tests pass against its installed package on Python 3.12, from outside the source checkout with checkout PYTHONPATH unset.
- The installed shared coordinator/demo smoke passes and confirms saved Off after restart. Official SDK 2.3.0 stdio subprocess plus shared and standalone replay checks pass separately. Test service settings are explicitly temporary; no owner configuration or actual host account is changed.
- The actual source launcher starts a real local HTTP service, accepts explicit On then Off, shuts down and restarts with Off retained. This uses only packaged synthetic source and temporary private state; no Ollama inventory/generation or cloud calls occur.
- Both synthetic retrieval variants pass; the bundled evidence-only Task Lab retains required spans in 10/10 mechanical cases. JavaScript syntax and a behavioral API-adapter check pass. These do not measure model reasoning.
- Diff whitespace checks pass. Fresh browser visual/accessibility acceptance and hosted CI for this candidate remain pending; prior main CI and historical browser observations do not establish those checks for this change.

## Remaining work

Finish the separate reviews of earlier exposed real-model runs, qualify one actual host connection, freeze genuinely unseen independent cases and run the paired final-task comparison. Full hardware/runtime/settings profile binding, persistent profiles, durable job recovery, guided source setup, sensitive-source/export policy, independent security/dependency/license review, broader accessibility/device support, Windows equivalence and whole-task savings remain open.

No actual unseen qualification study or new real-model accuracy experiment was performed for this implementation. A dataset labeled held_out by its owner is not proof of blindness or model promotion authority. No real profile was promoted.
