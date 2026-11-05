# Visual workbench: 0.4.0.dev6

The owner selected the third proposed design: a graphite workbench with amber actions, a project/history rail, broad task composer and paired exact-source panels. It runs on the recovered application's existing controller and bounded child, using Python's standard library and bundled HTML/CSS/JavaScript/SVG. No external frontend service, fonts, icon service or business application is required.

## Open and prepare

```bash
PYTHONPATH=src python3 -B -m shake_bake gui
```

The bundled inert demo needs no model. Add owner-approved folders at launch with `--project my-project=/absolute/folder` and a routing policy outside source roots with `--policy /absolute/owner-policy.json`. The UI cannot expand these grants. Up to eight projects include the demo. `--no-browser` and `--port 8422` are available; an installed wheel provides `shake-bake-ui`.

Choose a project and task type, enter the request and select Prepare for my assistant. Exact excerpts, line ranges and full-file hashes are visible; the original request, job identity, route explanation, cutoffs and usage are inspectable. Copy and JSON export refer to the pinned result even while a new task runs or fails. The JSON also retains the recovered coordinator's full native result, evidence identities and excerpt hashes. No final diagnosis is implied.

Documents currently means supported text files. PDF/image extraction, semantic embeddings and guided folder setup remain planned. Lexical selection is bounded and can omit relevant source. The current GUI does not provide explicit range selection.

## Local AI modes

Local AI off disables new model use and cancels this controller's owned active runner. It does not stop the separate Ollama daemon or attest GPU cancellation. Off also prevents inventory requests. Best tested selects only eligible owner-record profiles on comparable reviewed trials; the shipped candidates do not qualify. Model availability and reported digest are checked on use. No model is downloaded and no cloud-provider fallback exists.

For an explicit diagnostic candidate trial:

```bash
PYTHONPATH=src python3 -B -m shake_bake gui --allow-candidate-trials
```

In Model details, refresh inventory, choose Try a candidate, select an installed model and acknowledge unverified notes and the trusted cloud-disabled daemon requirement. The launch flag, enabled owner policy, acknowledgement and pinned digest are enforced outside the model. Native tools cannot select candidates or alter policy. A trial cannot promote a profile. Failures discard notes while retaining captured source; full task cancellation produces no new completed result.

Candidate notes remain separate from source. Structured-output/reference checks do not establish correctness. The client requests `think: false` and `keep_alive: 0`; returned thinking/tool output is refused. The daemon remains separately trusted. Published catalog statistics retain their source links and a distinct statement that no local qualification is inferred.

## State and boundaries

The browser remembers the original request draft, project/task/mode and selected candidate identity in localStorage. It does not persist captured source there. The checkbox follows the running controller's pause/policy state; pause and up to eight/five-minute jobs remain session-only. There is no SQLite/durable job recovery in this recovered runtime. Restart invalidates old task handles. Root grants and profile policy remain owner launch configuration.

The numeric-loopback service uses an HttpOnly SameSite cookie, Host/Origin/CSRF checks, a fixed asset allowlist and bounded request/connection handling. It is a trusted local owner session, not multi-user isolation or a public service. `--connection-file` publishes a private shared-adapter capability outside source; each host needs separate qualification. See [shared coordinator](shared-coordinator.md).

`tools/export_preview.py` captures only the bundled inert demo into self-contained HTML. It embeds local assets, marks the recorded state, refuses new jobs/model operations and permits inspecting/copying that recorded evidence. It is distinct from the live application.

Current browser, wheel, model and SDK observations are in [validation](validation-0.4.0.dev6.md) and [design QA](../design-qa.md). The archive import record remains historical and unchanged. Formal accessibility, wider devices, independent security, held-out accuracy, actual native-host UX and savings remain open.

## Explicit readiness checks

Inside Model details, expand This computer & selected model. Check this computer reads bounded local CPU/memory/GPU metadata without commands or network; it works with Local AI off. Check selected model reads the pinned candidate digest, Ollama version, quantization, context and capabilities without source or generation. It requires Local AI on; changing selection clears the old check. Values identify their observation origin/time and leave unknowns explicit. They do not qualify accuracy or prove memory fit. Full automatic tuning, installation identity and persisted qualified profiles remain planned.
