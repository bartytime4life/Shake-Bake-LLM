# What still needs proving

Reviewed November 4, 2026 for 0.4.0.dev4. Program tests do not replace the following trials.

[Known Issues](../KNOWN_ISSUES.md) tracks explicit security/reliability qualification gaps and release blockers. The [PC checklist](PC-CHECKLIST.md) contains the corresponding pending gates. These records do not claim a completed independent security audit or newly validated vulnerabilities.

| Gap | Why it matters | Current handling / next evidence |
| --- | --- | --- |
| Real model quality | A confident local mistake can make the host less accurate. | Outputs stay unverified; shipped routing profiles remain candidates. Use the trial runner, then an unseen paired evaluation. |
| Native-host comparison | Claude/ChatGPT may already do the preparation well. | Compare native host, deterministic evidence, and model-assisted evidence with identical tasks/source. Judge final answers. No host connection is qualified yet. |
| Retrieval blind spots | Excerpts can omit the decisive branch. | Exact spans and cutoffs are tested; finite lexical windows remain incomplete. Add unseen cross-file and large-repository tasks. |
| Evaluation contamination | Known questions or repeated cases inflate apparent strength. | Exposed-development labels and unique-case counts; keys outside fixture roots. Unseen data and independent review remain needed. |
| Failure accounting | Dropping slow or invalid attempts inflates accuracy. | Checkpoint attempts; failures count in reviewed accuracy. Unknown usage stays unknown. No automatic model substitution or retry. |
| Interrupted or changed runs | Different source/model states may be incomparable. | Freeze plan and identities; stop detected changes; save Ctrl+C results. Hard-crash resume remains unimplemented. |
| Hardware and tuning | A leaderboard does not establish local memory fit or quality after quantization. | Record model/digest and requested settings; do not infer GPU performance. Controlled cold/warm and memory trials remain needed. |
| Per-PC calibration | A good profile on one machine may perform differently on another. | Manual trial/checklist now; automatic tuning, persistent per-device profiles and hardware/runtime identity enforcement are planned in per-pc-calibration.md. |
| Visual/accessibility checks | Working APIs do not establish usable desktop or phone controls. | Responsive CSS and reduced motion are implemented. Automatic approval review blocked cloud-browser inspection because it could expose project data; no alternate browser route was attempted. Local visual and assistive-technology review remains pending. |
| Setup boundaries | Defaults can expose source or imply an unproven model won. | Loopback app, metadata-first checks, explicit roots and unqualified labels. Windows, guided setup and automatic downloads remain pending. |
| Sensitive data | Exact evidence can contain private material. | No automatic cloud client; copy/export is explicit. Owners choose permitted roots. Complete secret detection and daemon network isolation are not provided. |
| Licensing and updates | Terms, candidate tags and benchmark conditions change. | Keep publisher links separate from local results; recheck licenses/tags before shipping downloads. No universal best-model or free-compute claim. |
| Review provenance | An edited review record does not prove correctness. | Policies outside inspected roots; matching records required. Review identity is self-asserted. Authenticated independent promotion remains future work. |

The next useful experiment is one installed model over a small known case, followed by human review. Expand after actual responses and failures are recorded correctly. The helper remains preparation for the main assistant's reasoning; no deployment or production-readiness claim follows from these checks.
