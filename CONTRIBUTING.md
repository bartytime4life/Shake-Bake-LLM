# Develop and verify

Use Linux and Python 3.11+. The examples use Python 3.12 explicitly; an unsupported default `python3` can produce misleading failures. The core uses only the standard library; tests use temporary synthetic projects and simulated model services. No Ollama installation, cloud account, optional SDK or other application is needed for core checks. [Current status](docs/current-status.md) pins the documented dev37 source and separates previous validation, merge and installed state.

```bash
sb_checkout="$PWD"
PYTHONPATH=src python3.12 -B -m unittest discover -s tests -v
PYTHONPATH=src python3.12 -B benchmarks/evaluate_selection.py
PYTHONPATH=src python3.12 -B benchmarks/run_task_lab.py --evidence-only
node --check src/shake_bake/web/app.js
node --check src/shake_bake/web/troubleshoot.js
node scripts/frontend_smoke.cjs
node scripts/file_launch_test.cjs
node scripts/model_readiness_test.cjs
node scripts/clipboard_test.cjs
node scripts/browser_server_test.cjs
node scripts/request_timeout_test.cjs
```

Node runs developer JavaScript checks. It is not an application runtime dependency. Worker regression tests also verify that incompatible or malformed thinking controls refuse before source transmission while retaining exact evidence; legacy missing controls remain unknown. See [the dated compatibility evidence](docs/validation-0.4.0.dev8.md). The evidence-only lab verifies required source spans, hashes, cutoffs and unchanged fixtures; it does not grade a real model or assistant answer. CI repeats these checks on Python 3.11–3.14 and verifies source/installed browsers and an installed wheel. See [.github/workflows/ci.yml](.github/workflows/ci.yml) for exact commands/pins and [current status](docs/current-status.md) for observed runs; a configured matrix alone is not a passing run.

## Build and verify a wheel

CI pins setuptools 84.2.1 and wheel 0.48.0. Build tools are separate from runtime dependencies. A dependency-enabled development machine can install those versions in a build environment. Use a fresh installation-test environment and select only the wheel for the current version; an old `dist/*.whl` wildcard can select multiple builds.

```bash
sb_checkout="$PWD"
python3.12 -m venv .venv
.venv/bin/python -m pip install 'setuptools==84.2.1' 'wheel==0.48.0'
.venv/bin/python -m pip wheel --no-deps --no-build-isolation --no-index . --wheel-dir dist
.venv/bin/python scripts/verify_wheel.py
python3.12 -m venv /tmp/shake-bake-wheel-test
/tmp/shake-bake-wheel-test/bin/python -m pip install --no-deps --no-index dist/shake_and_bake_assistant-0.4.0.dev37-py3-none-any.whl
```

The filename above is for this guide's dev37 source; match it to `pyproject.toml` after a version change. The verifier requires exactly one wheel for that version and compares its packaged bytes. The build block saves the checkout path in `sb_checkout`; keep the quotes when using a path containing spaces. From outside the source checkout, with `PYTHONPATH` unset, verify installed behavior:

```bash
cd /tmp
env -u PYTHONPATH /tmp/shake-bake-wheel-test/bin/python "$sb_checkout/scripts/installed_smoke.py"
env -u PYTHONPATH /tmp/shake-bake-wheel-test/bin/shake-bake doctor
env -u PYTHONPATH /tmp/shake-bake-wheel-test/bin/python -B -m unittest discover -s "$sb_checkout/tests" -v
cd "$sb_checkout"
```

The wheel verifier compares all packaged code, web/demo assets and legal files with source bytes. The installed smoke uses the packaged demo, actual shared controller, loopback bridge and bounded child. It does not start a real model, connect a cloud host or qualify a browser.

## Optional MCP SDK gate

The current package pins the tested optional adapter to `mcp==2.3.0` (the imported archive used `mcp>=2,<3`). The earlier repository bootstrap's exact `mcp==2.3.0` input and hashed transitive lock are retained in `requirements/`; they are not new dependencies or redistributed SDK code. SDK 2.3.0 transport evidence is recorded in docs/validation-0.4.0.dev5.md. One actual Codex evidence-only demo now has scoped evidence; broader host qualification remains open. On a dependency-enabled machine, review the lock and upstream notices, then explicitly install it into a separate environment:

```bash
python3.12 -m venv /tmp/shake-bake-sdk-test
/tmp/shake-bake-sdk-test/bin/python -m pip install --require-hashes -r requirements/mcp.lock
/tmp/shake-bake-sdk-test/bin/python -m pip install --no-deps --no-index dist/shake_and_bake_assistant-0.4.0.dev37-py3-none-any.whl
cd /tmp
env -u PYTHONPATH /tmp/shake-bake-sdk-test/bin/python "$sb_checkout/integration/mcp_subprocess_smoke.py"
env -u PYTHONPATH /tmp/shake-bake-sdk-test/bin/python "$sb_checkout/integration/mcp_shared_smoke.py"
env -u PYTHONPATH /tmp/shake-bake-sdk-test/bin/python "$sb_checkout/integration/mcp_smoke.py"
cd "$sb_checkout"
```

The import-time SDK attempt exited 2 because the SDK was absent. The current candidate explicitly declares structured tool output and passes both recovered in-process checks plus `integration/mcp_subprocess_smoke.py` against an installed SDK/wheel. Run that subprocess check from outside the checkout with PYTHONPATH unset. The obsolete bootstrap `integration/mcp_stdio_smoke.py` targets a different API and is preserved in Git history only. Each actual host needs its own handoff, scope, failure and cancellation qualification after the SDK checks.

The [opt-in Codex host check](docs/codex-host-handoff.md) invokes a real cloud-backed assistant with the existing login and only the bundled inert demo. It is separate from these offline/SDK checks and must never be added to routine CI. Its `active-cancel` scenario temporarily stops only its own first preparation runner, verifies cancellation/refusals, then completes a fresh task. `tests/test_host_smoke.py` tests fabricated traces and the real local process gate without calling Codex or a model. Keep actual-host raw events and account-related logs private and outside Git.

## Evidence and publication

Preserve original requests, exact source, contradictions, omissions and unknown measurements. Keep model notes unverified. Use synthetic or owner-permitted sanitized reproduction material. Never promote a model, claim token savings or close a security/owner-PC gap from program tests alone.

Keep local policy, connection capabilities, captured private evidence, state, model files and build output out of Git. The archive checksum inventory in `docs/import/archive-MANIFEST.sha256` describes the recovered ZIP's original relative paths, not the evolving repository. Runtime/test parity was verified at import; future changes must carry their own tests and evidence.

For source UI startup use `./scripts/run-workbench`; it selects an installed Python 3.11+ without downloading one. Use a separate `--state-dir` outside inspected roots for development. Private evaluation datasets and run receipts belong outside the checkout; see docs/held-out-evaluation.md.

## Model readiness UI regression checks

`node scripts/request_timeout_test.cjs` checks browser request deadlines through headers and body, cleanup and uncertain task acknowledgements. Its optional argument is an installed app.js path. The workbench browser suite also checks stalled initialization/settings, an accepted task with a lost acknowledgement, and reconnection during active polling. See [browser request recovery](docs/request-recovery-2026-11-05.md) for the reproduction evidence and limits.

`node scripts/model_readiness_test.cjs` runs deterministic DOM-event and deferred-response checks without browser dependencies. Pass an installed `shake_bake/web/app.js` path as its optional argument to test wheel bytes.

The isolated `readiness-browser` CI job installs pinned Playwright 1.62.1 development tools and checks source and installed interfaces over loopback HTTP with synthetic metadata. To reproduce with Playwright available, run `node scripts/browser_readiness_test.cjs`, or append the isolated installed Python path. Readiness cases cover replacement, removal, empty/unavailable inventories, late success/failure, selection changes and Local AI off/on. Clipboard cases check native readback and manual recovery; the keyboard-copy case first writes and verifies a distinct marker. Dependency-free Promise checks cover delayed/failing/missing APIs, retry, job switching, exact text/layout identity and shared preparation activity. These synthetic checks do not call Ollama or establish model accuracy, owner-PC clipboard behavior in every browser, fit or speed.

For current measured outcomes and the difference between production settings and private diagnostic budgets, read [evaluation status](docs/evaluation-status.md). Update affected current guides and status pages when results change; retain dated experiment/acceptance records, failed attempts and original source requests. Public receipts use synthetic source and validated final notes; raw owner records and model reasoning stay private.

`node scripts/browser_workbench_test.cjs` checks settings, stale responses, connection recovery, history restoration after a real denial, initial mode gating, shared preparation, phone history, keyboard source scrolling and inert preview controls. The readiness, clipboard, workbench, excerpt-budget, failed-run and recovery scripts accept an isolated installed Python path as their first argument and `SB_CHROMIUM_EXECUTABLE=/absolute/path/to/chrome` for an existing Chromium binary with a fresh test profile; otherwise they use Playwright's managed browser. Source tests require `python3` on PATH to resolve to Python 3.11+: prepend the supported `.venv/bin` for source checks. Do not pass an uninstalled system interpreter as the installed argument, which deliberately unsets `PYTHONPATH`.

`node scripts/browser_troubleshoot_test.cjs` checks supported error formats, folder selection, exact input/source/exports, stale inputs, retained captured JSON, deadline/malformed/obsolete repeats, credentials and clipboard races. It automatically runs `browser_session_recovery_test.cjs`, including real service restarts; do not count those scenarios twice. `browser_excerpt_budget_test.cjs` checks a real preparation and exact export after whole-line byte fitting. None runs the recorded failing command or calls a model.

Run the five top-level browser scripts from the checkout root after making Playwright available:

```bash
export PATH="$PWD/.venv/bin:$PATH"
export NODE_PATH="/absolute/playwright-tools/node_modules"
node scripts/browser_readiness_test.cjs
node scripts/browser_clipboard_test.cjs
node scripts/browser_workbench_test.cjs
node scripts/browser_excerpt_budget_test.cjs
node scripts/browser_troubleshoot_test.cjs
```

Repeat those commands with `/tmp/shake-bake-wheel-test/bin/python` appended to test the isolated installed package. The [current validation table](docs/current-status.md) records 134 scenarios per source/installed pass, including recovery once. For documentation changes, check relative paths/fragments, executable command/flag names, current UI labels and source limits; preserve dated receipts, fixtures and owner requests. [The catalog](docs/catalog.md) identifies current guides, plans and immutable historical inputs.
