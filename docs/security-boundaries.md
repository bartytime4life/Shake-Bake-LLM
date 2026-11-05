# Security boundaries and remaining qualification

This is development software for one trusted local OS account on Linux. Inspected file names, source contents, local model output and host tool arguments can be hostile. Source text is data and is never executed, interpreted as policy, or used to choose additional roots. The owner controls configuration, optional qualification declarations and the local stdio host.

The collector enforces exact selections, descriptor-relative no-follow reads, file-type/hard-link checks, path exclusions, byte/line budgets, UTF-8 validation and source-change checks. The store requires owner-owned mode `0700`/`0600` directories/files and rejects symlinked state paths. Job/evidence access is scoped to a registered project and its captured root identity. A single cooperating coordinator owns each store.

These controls reduce reachable risks; they do not establish release security qualification. In particular:

- Secret detection is heuristic. Ordinary source may contain personal or sensitive information that does not resemble a credential. Review exported evidence before external handoff. Original user requests are preserved, not redacted.
- Access within a root is an explicit grant to the local collector, not a license or a grant to publish it. MCP tool results become visible to the connected host and may enter its provider context.
- No OS sandbox, mount isolation, process limit or network namespace is established. The default evidence path has no network or inspected-code execution; the optional worker and explicitly launched GUI/native services have the bounded local transports described below. Unrelated code in the same Python process retains its own authority.
- File I/O deadlines are cooperative. A blocked filesystem, hostile same-account process, compromised interpreter/kernel or maliciously replaced private SQLite files need separate analysis. Path/stat checks are not a proof against every concurrent filesystem mutation.
- Captures are individually checked file snapshots. They do not prove repository-wide consistency, Git revision identity or correctness of the requested task.
- Cancellation stops collection/model-client waiting cooperatively and discards late output. It does not prove that a separately managed local-model daemon stopped GPU work.
- SQLite stores exact private request/source text without application-level encryption. OS account protections and disk encryption remain external responsibilities. Archive or delete stores according to the source's retention requirements.
- The MCP transport is inherited local stdio; its shared mode additionally uses the private native Unix socket. No public/shared HTTP deployment or multi-user authentication is supplied. The optional SDK and transitive dependencies require continuing vulnerability and artifact review.

The explicitly launched GUI uses authenticated loopback HTTP, exact origin/CSRF checks, bounded request admission and connection deadlines. Shared native clients use a separately authenticated owner-only Unix socket/publication outside inspected roots. The GUI cannot register roots, edit qualification declarations or enable owner-disabled Ollama. Current connection, source-identity, pause and export behavior is described in [workbench.md](workbench.md).

The optional worker uses numeric loopback with no proxy, redirects or downloads. Reported remote/cloud models, stale identities, invalid notes and unsupported citations are refused. A client cannot attest a daemon's upstream behavior or loaded weight bytes. Private-source users must configure a trusted local-only daemon. Candidate schema/citation validity is not accuracy; the real synthetic trial itself produced an unsupported uncertainty, so no model is qualified. See [ollama-routing.md](ollama-routing.md).

Tests exercise specific positive/negative behavior. Independent boundary review, broader sustained-load/resource tests, actual host qualification and Windows equivalents remain open. No finding category is suppressed or declared acceptable by this document.
