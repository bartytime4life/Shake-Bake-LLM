# Visual workbench: 0.4.0.dev4

The graphical interface is a local browser application backed by the same evidence collector and accuracy-gated router. It uses Python's standard library, plain JavaScript, CSS and inline SVG; no external fonts, image servers or frontend dependencies are loaded. The current runtime targets Linux/Python 3.11+. Windows and physical owner-PC behavior remain unqualified.

## The user flow

1. Start `PYTHONPATH=src python3 -B -m shake_bake gui` from the extracted project. A browser opens to the local loopback service; use `--no-browser` when appropriate.
2. Choose an approved working folder and a task card: Code, Troubleshoot, Documents or Search. Accuracy remains the policy priority. The bundled demo needs no model download.
3. Enter the question and click Prepare my brief. A bounded child collects source and checks the task policy. One job runs at a time; the page shows the actual running/terminal state, not a fabricated progress percentage.
4. Inspect the evidence map and source cards. Every excerpt includes its path, line range, full-file/excerpt hashes and captured-state limitation. Source text is inserted as text, never interpreted as HTML.
5. Expand Why this model? or Why evidence only? and open a model card for details. Copy the evidence brief into Claude/ChatGPT, or download the captured result as JSON. Direct host connection remains unverified.

Documents currently covers supported text files. PDF/image extraction, semantic embedding search and automated setup/downloads are not implemented. The interface is not a general chat model replacement.

## Visuals and model disclosure

The interface uses an ink background, peach/mint/lavender accents, illustrated task cards, an animated conceptual handoff diagram and a live evidence map populated from captured source records. The top diagram explains the workflow; it is not inference telemetry. Source-map nodes open the corresponding source card. A four-step handoff panel reflects available results without claiming a completed host review.

Model panels separate author-published benchmarks from owner-recorded local trials. They show model tag, benchmark source/date, candidate role, selection explanation when applicable and known limits. A published score does not become a local measurement or automatic qualification. Current shipped profiles remain candidates. Valid owner records are labeled as records; live identity checks remain separate.

The layout includes compact-screen CSS and reduced-motion rules, visible focus states, labeled form controls, keyboard-operable disclosures and source-map nodes. Text-size adjustments were made for readability. Browser rendering, phone layout, keyboard/focus behavior, clipboard/download interactions and animation behavior have not been visually or interactively verified in a browser.

## Local boundaries and state

The server binds only to `127.0.0.1`. It validates Host, uses an HttpOnly/SameSite=Strict session cookie, checks same-origin CSRF headers on writes, limits request bodies and serves only a fixed asset allowlist. It is not a public hosted service or multi-user security boundary.

The server admits at most eight active connections, applies a three-second initial idle timeout and a cooperative twelve-second absolute connection deadline. Excess connections close with a best-effort 503. A controller request that times out is cancelled if still queued. See [connection-limit scope and tests](connection-limits.md). These controls do not establish sustained-load or multi-user security qualification.

A persistent owner thread launches and supervises trusted preparation children, so a short HTTP-request thread ending does not kill a running job. Sources are not executed or modified. Temporary task streams remain outside inspected roots. The workbench uses approved project IDs rather than accepting arbitrary file paths through task requests.

Add a folder at launch with `--project my-project=/absolute/folder`; up to eight total folders are supported, including the demo. A real owner policy must stay outside inspected roots. `--policy /absolute/owner-policy.json` selects it. Current setup uses these launch options; a native folder-picker/setup wizard remains future work.

The local-AI switch disables new model calls and cancels this workbench's active owned runner. It does not terminate the separate Ollama daemon or prove GPU-work cancellation. Session history and switch state last only for the running service; task access expires after five minutes/eight jobs. Question drafts are saved in browser localStorage. Captured source remains in session memory unless the user explicitly copies/downloads it.

## Recorded preview

`tools/export_preview.py` creates a self-contained HTML inspector from a real run of the bundled inert demo. The export has no project paths, session cookie, CSRF token, real-model output or user project data. It embeds CSS, SVG and JavaScript, labels itself Recorded demo preview, disables new-job/model operations, and supports inspecting the recorded evidence and model catalog. It is a design-review artifact, not a second live server.

The export deliberately contains the demo code and captured hashes so the user can inspect real evidence rather than invented results. Its published model numbers retain source links and pending local-trial labels.

## Verification and remaining limits

121 program tests pass. Real local HTTP checks cover assets, session/Host/Origin/CSRF checks, task admission, a child surviving its request thread, source preservation, model disclosure, owned-job cancellation, file-path restrictions and offline-export data/escaping. JavaScript syntax checks pass. A no-index wheel build includes the required GUI/demo assets.

Automatic approval review denied opening the local app in the cloud browser because the operation could expose application/project data to an unverified destination. No browser-policy workaround was attempted; the preview server was stopped. Consequently no desktop/mobile visual review or end-to-end browser interaction is claimed. Users can run the local app and inspect the recorded preview on their own device. Real Ollama inference, model accuracy, hosted handoffs and token savings remain pending.
