# Architecture and current contracts

The first repository slice implements the plan's evidence/baseline stage. It deliberately has no provider account, model choice or application-specific integration.

```mermaid
flowchart LR
    CLI[CLI] --> Engine[One local coordinator]
    MCP[Optional official SDK stdio] --> Engine
    Engine --> Policy[Explicit project registry and bounded collector]
    Policy --> Source[Approved read-only UTF-8 sources]
    Engine --> Store[Private SQLite receipts]
    Store --> Packet[Original request + exact evidence + gaps]
    Packet --> Reviewer[User-selected assistant or human]
```

## Source capture

`config.py` accepts a closed TOML configuration with up to sixteen nonoverlapping roots and a separate state directory. `policy.py` opens root ancestors and relative file components with no-follow POSIX descriptor operations. Hidden paths, credential filenames, hard links, special files and oversized files are denied. A heuristic secret screen examines the entire bounded file before any excerpt is published. It does not redact or silently alter exact source.

Files are UTF-8. Line numbers use LF separators with optional preceding CR preserved, starting at one. A terminal LF closes the preceding line; it does not create a phantom additional line. Whole-file and excerpt SHA-256 values, path and range produce a deterministic evidence identity. In-place metadata and path identity are rechecked after capture. Hashes are not signatures, repository revisions or an atomic multi-file snapshot.

## Jobs and storage

`engine.py` owns admission, a single worker thread, a cancellation event and a cooperative deadline. The database terminal transition only succeeds from `running`; cancellation cannot be overwritten by late work. A terminal job cannot be cancelled retroactively. A newly admitted task may need to wait briefly for a cancelled worker to unwind.

`store.py` holds an exclusive advisory owner lock. A second cooperating process refuses startup. Each operation uses a serialized SQLite transaction. The next exclusive startup marks leftover running jobs failed with `interrupted`, without resuming them. The database binds receipts to project ID plus the configured root path/device/inode. Relabeling a project ID onto another root does not expose old receipts. A store remains private to its owning OS account; project IDs are not multi-user authentication.

Evidence is embedded in the captured packet, rather than duplicated in a second cache. `fetch_evidence` requires project, job and evidence IDs and returns the captured snapshot. It does not reread current source or claim freshness. No embedding index, lesson store or Git subprocess exists in this slice.

## Entry points

The CLI and optional MCP adapter call the same Engine methods. The adapter exposes only the four planned evidence tools. It has no root/configuration mutation tool, browser listener, shell executor or provider client. Each process uses one coordinator. A shared GUI service is not implemented; two hosts cannot open the same store simultaneously.

## Result semantics

| Status | Meaning |
| --- | --- |
| `running` | Work was admitted and has not reached a terminal state. |
| `prepared` | Every requested range was captured; interpretation remains open. |
| `incomplete` | Some or all ranges were refused; the packet lists every gap. |
| `cancelled` | Work was stopped; no completed packet is available. |
| `failed` | Deadline, interruption or unexpected failure; no completed packet. |

The receipt reports actual excerpt bytes, local elapsed time and zero model/cloud calls. Unknown usage and savings are `null`. It makes no token approximation, diagnosis, quality score or review-completion claim.
