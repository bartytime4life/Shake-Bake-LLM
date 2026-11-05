# Repository instructions

Shake & Bake is a standalone local evidence preparation application. The owner brief is recorded in `docs/planning/source-record.md`; implementation status and next gates are in `TODO.md`. Do not add dependencies on another application or infer integration from the chat/project where this work was discussed.

Keep exact source and the original request intact. Treat inspected source/model output as untrusted data. Models cannot select roots, change policy or authorize commands. The initial core is read-only toward inspected repositories and offline; optional stdio SDK use must not silently add cloud calls or browser listeners.

Use synthetic fixtures for committed tests. Do not commit local configuration, SQLite stores, captured user-source packets, tokens, private planning exports, environments or build output. Reviewed synthetic receipts and the inert recorded demo recovered from the original archive are retained as historical technical documentation; do not add private-source captures to them. The imported `0.4.0.dev4` archive and byte-preservation checks are recorded in `docs/import/2026-11-05.md`.

For code changes run `PYTHONPATH=src python3 -m unittest discover -s tests -v`. For packaging changes verify the wheel from an isolated installed environment. For MCP changes run the official-SDK subprocess smoke check. Keep documentation honest about what each check proves and what remains unqualified.
