# Local web connection limits

The dev37 source retains the controls introduced in dev3 below. See [current status](current-status.md) for the reviewed source and later validation, and [the HTTP reference](api-reference.md) for current endpoints/authentication. These controls bound selected local-web failure modes; they are not a complete denial-of-service defense, a multi-user authorization boundary or a completed security qualification.

## Implemented behavior

| Control | Default | Scope |
| --- | --- | --- |
| Active HTTP handlers | 8 | Excess accepted connections receive a best-effort 503 and close without allocating a handler thread. The listen backlog is also bounded. |
| Initial socket idle timeout | 3 seconds | Set before parsing the request line or headers. Body reads also retain their existing timeout. |
| Absolute connection deadline | 12 seconds | Covers request parsing, body and response lifetime; a slow drip cannot hold a slot indefinitely by resetting the idle timer. Checked cooperatively by the server loop, normally every 0.2 seconds; not a realtime guarantee. |
| Controller wait | 8 seconds | An expired request cancels its future if it is still queued. It cannot silently start a queued task/settings operation later. Already-running operations retain their own bounds. |
| Server close | Disconnect active sockets | Incomplete connections are shut down; normal handler cleanup releases admission slots. |

These settings are server-side defaults. They are not new user-facing tuning controls. Bounded asynchronous preparation jobs keep their separate task deadlines. An HTTP poll disconnecting does not terminate an already running helper job or prove that Ollama stopped GPU work. The normal interface can poll again for the job's actual status.

An overload response is best effort: if the local peer cannot receive it immediately, the socket closes. A client may see a transport error rather than JSON. This path never creates a session cookie or executes a task. It is intended to keep connection pressure bounded, not promise uninterrupted availability under continuous local flooding.

## Original dev3 regression evidence

Six tests use actual loopback sockets and the real server/controller:

1. An idle request is disconnected and normal GETs recover.
2. Headers dripped faster than the idle timeout still hit the absolute deadline.
3. Connections beyond the configured cap get refused without consuming an additional handler slot; normal requests recover when held sockets close.
4. An incomplete authorized body expires without starting a task.
5. Server close disconnects an incomplete request.
6. A queued task whose controller wait expires is skipped without spawning work.

Tests shorten deadlines to keep checks bounded; normal defaults stay as above. The original dev3 development suite passed 102 program tests. That count is historical; [current status](current-status.md) records the later 516-test baseline and its separate browser/installed checks. These are development-environment measurements, not owner-PC load results, real-model accuracy or independent security-audit evidence.

## Remaining work

SEC-04 remains open in KNOWN_ISSUES.md. Broader malformed-input coverage, sustained representative load, parent-process memory measurements, real-machine behavior and an independent review still need evidence. Local users/processes are not isolated from each other by these controls. Secret handling, dependency/update provenance and actual host/model qualification remain separate open items.
