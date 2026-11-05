# Develop and verify

Use Linux and Python 3.11+. The core uses only the standard library; tests use temporary synthetic projects and simulated model services. No Ollama installation, cloud account, optional SDK or other application is needed for core checks.

```bash
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
PYTHONPATH=src python3 -B benchmarks/evaluate_selection.py
PYTHONPATH=src python3 -B benchmarks/run_task_lab.py --evidence-only
node --check src/shake_bake/web/app.js
node scripts/frontend_smoke.cjs
```

Node is only a developer JavaScript syntax check. It is not an application runtime dependency. The evidence-only lab verifies required source spans, hashes, cutoffs and unchanged fixtures; it does not grade a real model or assistant answer. CI repeats these checks and verifies an installed wheel. See `.github/workflows/ci.yml` for the exact commands and pinned action revisions. Local import evidence covers Python 3.12; other CI matrix results must be observed separately.

## Build and verify a wheel

The import was built with setuptools 84.2.1 and wheel 0.48.0. Build tools are separate from runtime dependencies. A normal dependency-enabled development machine can install those exact versions in a build environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install 'setuptools==84.2.1' 'wheel==0.48.0'
.venv/bin/python -m pip wheel --no-deps --no-build-isolation --no-index . --wheel-dir dist
.venv/bin/python scripts/verify_wheel.py
python3 -m venv /tmp/shake-bake-wheel-test
/tmp/shake-bake-wheel-test/bin/python -m pip install --no-deps --no-index dist/*.whl
```

Use an empty output directory so there is exactly one candidate wheel. From outside the source checkout, with `PYTHONPATH` unset, verify installed behavior:

```bash
cd /tmp
env -u PYTHONPATH /tmp/shake-bake-wheel-test/bin/python /absolute/checkout/scripts/installed_smoke.py
env -u PYTHONPATH /tmp/shake-bake-wheel-test/bin/shake-bake doctor
```

The wheel verifier compares all packaged code, web/demo assets and legal files with source bytes. The installed smoke uses the packaged demo, actual shared controller, loopback bridge and bounded child. It does not start a real model, connect a cloud host or qualify a browser.

## Optional MCP SDK gate

The current package pins the tested optional adapter to `mcp==2.3.0` (the imported archive used `mcp>=2,<3`). The earlier repository bootstrap's exact `mcp==2.3.0` input and hashed transitive lock are retained in `requirements/`; they are not new dependencies or redistributed SDK code. SDK 2.3.0 transport evidence is recorded in docs/validation-0.4.0.dev5.md. One actual Codex evidence-only demo now has scoped evidence; broader host qualification remains open. On a dependency-enabled machine, review the lock and upstream notices, then explicitly install it into a separate environment:

```bash
python3 -m venv /tmp/shake-bake-sdk-test
/tmp/shake-bake-sdk-test/bin/python -m pip install --require-hashes -r requirements/mcp.lock
/tmp/shake-bake-sdk-test/bin/python -m pip install --no-deps --no-index dist/*.whl
env -u PYTHONPATH /tmp/shake-bake-sdk-test/bin/python integration/mcp_smoke.py
env -u PYTHONPATH /tmp/shake-bake-sdk-test/bin/python integration/mcp_shared_smoke.py
```

The import-time SDK attempt exited 2 because the SDK was absent. The current candidate explicitly declares structured tool output and passes both recovered in-process checks plus `integration/mcp_subprocess_smoke.py` against an installed SDK/wheel. Run that subprocess check from outside the checkout with PYTHONPATH unset. The obsolete bootstrap `integration/mcp_stdio_smoke.py` targets a different API and is preserved in Git history only. Each actual host needs its own handoff, scope, failure and cancellation qualification after the SDK checks.

The [opt-in Codex host check](docs/codex-host-handoff.md) invokes a real cloud-backed assistant with the existing login and only the bundled inert demo. It is separate from these offline/SDK checks and must never be added to routine CI. `tests/test_host_smoke.py` tests its validator using fabricated synthetic traces without calling Codex. Keep actual-host raw events and account-related logs private and outside Git.

## Evidence and publication

Preserve original requests, exact source, contradictions, omissions and unknown measurements. Keep model notes unverified. Use synthetic or owner-permitted sanitized reproduction material. Never promote a model, claim token savings or close a security/owner-PC gap from program tests alone.

Keep local policy, connection capabilities, captured private evidence, state, model files and build output out of Git. The archive checksum inventory in `docs/import/archive-MANIFEST.sha256` describes the recovered ZIP's original relative paths, not the evolving repository. Runtime/test parity was verified at import; future changes must carry their own tests and evidence.

For source UI startup use `./scripts/run-workbench`; it selects an installed Python 3.11+ without downloading one. Use a separate `--state-dir` outside inspected roots for development. Private evaluation datasets and run receipts belong outside the checkout; see docs/held-out-evaluation.md.
