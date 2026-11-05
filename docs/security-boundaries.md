# Security boundaries and remaining qualification

This is a development bootstrap for one trusted local OS account on Linux. Inspected file names, source contents and host tool arguments can be hostile. Source text is data and is never executed, interpreted as policy, or used to choose additional roots. The owner controls configuration and the local stdio host.

The collector enforces exact selections, descriptor-relative no-follow reads, file-type/hard-link checks, path exclusions, byte/line budgets, UTF-8 validation and source-change checks. The store requires owner-owned mode `0700`/`0600` directories/files and rejects symlinked state paths. Job/evidence access is scoped to a registered project and its captured root identity. A single cooperating coordinator owns each store.

These controls reduce reachable risks; they do not establish release security qualification. In particular:

- Secret detection is heuristic. Ordinary source may contain personal or sensitive information that does not resemble a credential. Review exported evidence before external handoff. Original user requests are preserved, not redacted.
- Access within a root is an explicit grant to the local collector, not a license or a grant to publish it. MCP tool results become visible to the connected host and may enter its provider context.
- No OS sandbox, mount isolation, process limit or network namespace is established. The core has no network or inspected-code execution path; that does not stop unrelated code in the same Python process from using its own authority.
- File I/O deadlines are cooperative. A blocked filesystem, hostile same-account process, compromised interpreter/kernel or maliciously replaced private SQLite files need separate analysis. Path/stat checks are not a proof against every concurrent filesystem mutation.
- Captures are individually checked file snapshots. They do not prove repository-wide consistency, Git revision identity or correctness of the requested task.
- Cancellation stops collection cooperatively and discards late output. It does not stop a local-model daemon, since no such worker exists here.
- SQLite stores exact private request/source text without application-level encryption. OS account protections and disk encryption remain external responsibilities. Archive or delete stores according to the source's retention requirements.
- MCP runs only on inherited local stdio; no public/shared HTTP deployment or multi-user authentication is supplied. The optional SDK and transitive dependencies require continuing vulnerability and artifact review.

Tests exercise specific positive/negative behavior. Independent boundary review, sustained-load/resource tests, actual host qualification and Windows equivalents remain open. No finding category is suppressed or declared acceptable by this document.
