# Local workbench HTTP reference

This is the internal loopback browser/bridge contract in dev37, not a public or multi-user API. `gui.py` binds `127.0.0.1`; use [official stdio/shared setup](shared-coordinator.md) for an assistant host. See [current status](current-status.md), [architecture](architecture.md) and [helper methods](helper-contract.md) for the corresponding source identity and boundaries.

## Browser session

`GET /` serves the local page and sets the HttpOnly, SameSite=Strict `sb_session_<bound-port>` cookie. Static assets are served locally. Authenticated API GETs require the exact permitted Host and session cookie, refuse cross-site fetches, and validate Origin when present. Browser POSTs additionally require a permitted local Origin and the current `X-SB-CSRF` value returned by `GET /api/state`. The permitted Host/Origin sets use localhost and 127.0.0.1 at this server's bound port. CSRF/session values are capabilities; do not put them in source, logs, examples or public documentation.

Session tokens rotate on service restart, which also loses session-only folder approvals and service jobs. This open tab fetches the root page for renewal only after explicit **Retry connection**, using a bounded same-origin request followed by authenticated state. It does not reload the page or replay a POST. Another tab opening the root can also refresh the shared cookie. Cookie renewal on the same running service does not revoke that service's projects/jobs; a changed service identity invalidates old response ownership and missing approvals must be explicitly reconnected.

## Endpoints

POST bodies are JSON objects with `Content-Type: application/json` and a positive Content-Length. The fields below are native HTTP fields; `/api/start`, `/api/result`, `/api/cancel`, `/api/pause`, `/api/models` and `/api/preferences` are browser JavaScript conveniences, not server endpoints. `/api/preferences` writes browser preferences locally.

| Method/path | Request | Response/purpose |
| --- | --- | --- |
| `GET /api/state` | No body | Version, approved projects, recent task metadata, Local AI/policy state, catalog/inventory metadata, CSRF token and shared-mode flag |
| `POST /api/projects` | `label`, `path` | Approve an existing absolute folder for read-only use in this service session; returns validated project identity. No assistant scope expansion. |
| `POST /api/tasks` | `project_id`, exact `task`, `task_kind`; optional `candidate` | HTTP 202 with `task_id` and state; acceptance does not mean completion. Task kinds: code, troubleshoot, documents, search. |
| `GET /api/tasks/<task_id>` | A 32-character lowercase hexadecimal task ID | Actual native state/outcome and retained result. Browser results include exact captured evidence when available. |
| `POST /api/tasks/<task_id>/cancel` | `{}` | Cancel that owned task if applicable; cancellation is not proof that a separate model daemon stopped work. |
| `POST /api/troubleshoot` | `project_id`, exact `error_output`, `command`; optional `working_directory` | Synchronous bounded `failure_source_report`, including project, original inputs, frames/errors, source hashes and limits. Never executes the command. |
| `POST /api/settings` | `enabled`: boolean | Confirm shared Local AI on/off; normal launch persists this boolean privately. Failed saving pauses AI in the current process. |
| `POST /api/inventory` | `{}` | Explicit installed-model metadata refresh; no generation/download. Paused AI returns paused state. |
| `POST /api/computer` | `{}` | Local capability metadata; no Ollama request or measured model fit. |
| `POST /api/model-check` | Exact `model`, 64-character lowercase hexadecimal `digest` | Check selected identity/runtime metadata while Local AI/policy permits it; no source/generation is sent. |

An explicitly acknowledged candidate has `model`, pinned `digest` and `acknowledged: true`. It additionally requires owner-enabled candidate trials and enabled Local AI/policy. Supplying a model name does not qualify it, expand a root or override policy.

For example, the native task payload below requests only synthetic bundled evidence:

```json
{"project_id":"starter-demo","task":"Find the executable slice coverage guard.","task_kind":"code"}
```

`recent` retains native `state` separately from `outcome` and `evidence_available`. A `DONE` result with `DENY`/`ERROR` is failed, not prepared. `ANSWER`/`ABSTAIN` with excerpts is prepared evidence; without excerpts it is incomplete. The browser labels older completion metadata without those facts completed and leaves it manually reviewable. These labels do not claim a verified answer.

## Private shared bridge

`POST /api/helper` is enabled only when the owner publishes a shared connection. It uses the private `Authorization: Bearer ...` capability, requires the permitted Host, and refuses browser Origin or Sec-Fetch-Site headers. Its JSON payload is `{"method": "...", "arguments": {...}}`; the response wraps the method result as `{"result": {...}}`. A method refusal is a structured `DENY` result inside HTTP 200. This authentication is separate from the browser cookie/CSRF path.

The bridge exposes the five scoped helper methods documented in [the helper contract](helper-contract.md). Its permitted projects are fixed by the owner at publication; browser folder connection does not grant access. Connection files/tokens stay outside inspected projects and Git. This trusted-owner loopback design does not isolate hostile local users/processes.

## Bounds and errors

| Boundary | Current limit |
| --- | --- |
| Serialized task/ordinary POST input | 128 KiB |
| Task field | Nonempty valid UTF-8 text, at most 16,384 characters; the serialized request must also fit its byte cap |
| Serialized failed-run POST input | 512 KiB, including JSON encoding; individual fields still have smaller limits |
| Failed-run field limits | Error 64 KiB UTF-8; command and working folder 4 KiB UTF-8 each; no silent truncation |
| Runner result transport | 1 MiB; overflow returns an explicit error rather than altered evidence |
| Concurrent source tasks | One per helper session; retained source jobs at most eight, approximately five minutes |
| HTTP admission/time | Eight handlers, initial idle 3s, cooperative connection deadline 12s, controller wait 8s |
| Browser request deadline | 15s through headers and JSON body; timeout does not prove the operation did not run |

See [connection limits](connection-limits.md) and [source checks](failed-run-workflow.md) for resource/process and source budgets. A failed-run request refuses a busy source-preparation session rather than running a competing source check.

Browser refusal responses generally use HTTP 400 with `{"error":"<code>"}`; authentication/Host refusals use 403, unknown paths 404 and unexpected service failures 503. Admission overload may close the socket instead of delivering JSON. Codes such as `helper_busy`, `unknown_or_expired_task`, `working_directory_unavailable` and `workbench_request_timeout` need their own recovery action. Do not automatically retry task starts, settings, root approval or model work after an uncertain response. Refresh actual state and require an explicit new action.

The failed-run browser retains its prior accepted report through a failed recheck. Captured JSON serializes that report, not edited inputs. A response must match the submitted error, command, working folder and project identity and remain current for both input revision and session generation before replacing it.
