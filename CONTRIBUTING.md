# Development

Use Python 3.11+ on Linux. The source core has no external runtime dependencies. Keep local configuration, captured evidence, databases, credentials and recovered planning exports out of Git. Use synthetic or explicitly permitted sanitized material in committed tests.

## Core checks

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src
```

Boundary tests check exact byte preservation, refusal of hostile paths/file types, secret screens, in-place/path replacement, scoped persistence, exclusive ownership, cancellation and late results. Mocked no-network/no-process checks are bounded regression evidence, not OS isolation.

## Build and test an installed wheel

```bash
python3 -m venv .venv
.venv/bin/python -m pip install build 'setuptools>=77'
.venv/bin/python -m build --wheel --no-isolation
python3 -m venv /tmp/shake-bake-wheel-test
/tmp/shake-bake-wheel-test/bin/python -m pip install dist/*.whl
/tmp/shake-bake-wheel-test/bin/shake-bake doctor
/tmp/shake-bake-wheel-test/bin/shake-bake demo
```

Run installed checks from outside the source checkout and remove `PYTHONPATH` to prevent accidental source imports. The CI definition does this and verifies wheel license/notice and fixture bytes.

For optional SDK qualification, install [the hashed lock](requirements/mcp.lock) before the wheel's `mcp` extra, then run [the stdio integration script](integration/mcp_stdio_smoke.py). Regenerate the lock deliberately with `uv pip compile --generate-hashes requirements/mcp.in -o requirements/mcp.lock`; review dependency/version changes and rerun qualification.

Also run `integration/mcp_shared_smoke.py --python /path/to/installed/python` for GUI/shared-native changes. It uses a real installed GUI service and official SDK subprocess over private IPC, with inert source and local AI paused; no real model is required. Actual model trials are opt-in and belong in separate records. Keep captured packets, private connection publications and browser artifacts outside Git.

The v0.2 store migrates schema v1 receipts to v2 and adds private preferences/installation identity. Older v0.1 code refuses schema v2. Preserve a store backup before an upgrade if you need an older binary for rollback; never rewrite evidence identities to bypass root scope.

## Evidence standards

Keep source facts separate from model interpretations. Preserve the user's exact request, necessary caveats, contradictory results, exact source and missing evidence. `prepared` is source capture, not task success. Do not add measured-performance, compatibility, licensing or security claims without corresponding recorded evidence.

Avoid unapproved network/provider fallback, implicit model downloads, arbitrary shell execution and source-driven permission changes. Review architecture and negative cases before adding a new adapter. Keep the core standalone and package optional integrations separately.
