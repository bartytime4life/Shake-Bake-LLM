# Standalone local workbench

Run the bundled inert demo:

```bash
PYTHONPATH=src python3 -m shake_bake gui
```

After installation, `shake-bake gui` and `shake-bake-gui` are equivalent. Use `--no-browser` to print a private launch link; `--port` selects a loopback port. The default is 8421. Default state is `~/.local/state/shake-bake`; `--state-dir` changes the demo store. For an intentional installed-model trial on synthetic data, add `--enable-local-ai`.

The bundled demo is copied into a versioned private sibling of the state directory. These are app-owned inert files with one link each, so package-manager cache hard links never require relaxing source policy. Normal restarts reuse an unchanged copy; owner-modified demo files are preserved and refused rather than overwritten. A fresh state path creates a fresh demo.

For real projects use `--config /path/to/config.toml`. Root grants and the optional Ollama permission come from that owner-controlled configuration; the web page cannot register roots or enable an owner-disabled integration. The GUI and its icons ship in the Python wheel and use no CDN, frontend development server, account or other application dependency.

## Workflow

Choose an approved project, task category and original request, then Prepare for my assistant. Bounded lexical discovery selects source windows; optional exact ranges live inside Model details. A completed result is pinned to its original request, project and job ID. Preparing, failing or cancelling a newer task does not relabel an earlier brief as the new result.

Model details contains the local-AI modes, installed inventory refresh, saved candidate/digest and qualification explanation. Local AI starts off unless an earlier explicit preference was saved. No inventory or inference occurs merely from restoring preferences or opening the page. A deliberate candidate trial requires its acknowledgement again in each browser session. A model selection survives restart/offline inventory. The off switch pauses this session's model work and saves an off preference, while source preparation remains usable.

Copy brief and Download JSON export the **pinned** job, including original request, exact source, missing evidence, separate unverified model notes, routing and usage receipt. Those exports may contain private source. Review them before giving them to a host/provider. The application does not send them to Claude/ChatGPT by itself.

Recent briefs are scoped to the registered roots and persisted in the local SQLite store. Draft task text/ranges are browser-session inputs; saved preferences are separate. Browser session tokens and the local-AI pause are service-session state, not a promise to persist across a restart.

## Shared native coordinator

The GUI owns the Engine and its exclusive store lock. It publishes an owner-only `connection.json` beside a `native.sock` Unix socket, both mode `0600`, inside the private `0700` state directory. A native MCP process can use that same coordinator:

```bash
shake-bake-mcp --connect /absolute/private/state/connection.json
```

Only `start_job`, `get_result`, `fetch_evidence` and `cancel_job` are exposed. Native and browser entry points share actual job admission, routing, source/evidence identity and the session local-AI pause. Closing one native client does not cancel service jobs. The optional `--config` MCP mode still owns a separate diagnostic coordinator and cannot share the same store concurrently.

The connection publication is local application authentication material. Do not copy it into a host conversation, inspected project, source packet or Git. Normal shutdown removes the service's own unchanged publication/socket. Hard stops can leave stale files; verify the previous service is stopped before explicitly archiving them. Owner-replaced publications are preserved. Unix socket paths have a length limit; the service refuses an overly long private state path.

## Browser boundary

HTTP binds numeric loopback only. Public static bootstrap/assets contain no inspected source. API access requires the private launch token exchanged for an HttpOnly SameSite cookie. Mutations additionally require exact Host/Origin and a session CSRF value; cross-site API requests are denied. The fragment token is removed from the address bar. Content Security Policy limits assets and connections to this origin; no permissive CORS or public tunnel is supplied.

The server admits eight active connections, has a three-second idle read timeout, a cooperative twelve-second absolute connection deadline and bounded JSON bodies. Excess connections are refused before creating a handler. The private native socket has separate bounded admission, framing, authentication and time limits. These are application checks, not OS isolation, internet flood resistance or multi-user authentication.

Stop with Ctrl+C. Private state remains available for the next launch; incomplete jobs become failed, not automatically resumed. Do not expose this development server publicly. Actual Claude/ChatGPT host UX, independent security qualification and Windows equivalents remain unqualified.
