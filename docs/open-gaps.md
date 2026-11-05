# What still needs proving

Reviewed November 5, 2026 for 0.4.0.dev7. Program tests do not replace the following trials.

[Known Issues](../KNOWN_ISSUES.md) tracks explicit security/reliability qualification gaps and release blockers. The [PC checklist](PC-CHECKLIST.md) contains the corresponding pending gates. These records do not claim a completed independent security audit or newly validated vulnerabilities.

| Gap | Why it matters | Current handling / next evidence |
| --- | --- | --- |
| Real model quality | A confident local mistake can make the host less accurate. | Outputs stay unverified; shipped routing profiles remain candidates. Exposed `.dev6` model runs found incorrect claims; full semantic review is pending. Use the external-dataset runner, then a genuinely unseen paired final-task evaluation. |
| Native-host comparison | Claude/ChatGPT may already do the preparation well. | Compare native host, deterministic evidence, and model-assisted evidence with identical tasks/source. Judge final answers. No host connection is qualified yet. |
| Retrieval blind spots | Excerpts can omit the decisive branch. | Exact spans and cutoffs are tested; finite lexical windows remain incomplete. Add unseen cross-file and large-repository tasks. |
| Evaluation contamination | Known questions or repeated cases inflate apparent strength. | External datasets, explicit owner-declared splits, pinned inputs, key isolation and unique-case counts are implemented. Genuinely unseen data, independent review and the paired host study remain needed. |
| Failure accounting | Dropping slow or invalid attempts inflates accuracy. | Checkpoint attempts; failures count in reviewed accuracy. Unknown usage stays unknown. No automatic model substitution or retry. |
| Interrupted or changed runs | Different source/model states may be incomparable. | Freeze plan and identities; stop detected changes; save Ctrl+C results. Hard-crash resume remains unimplemented. |
| Hardware and tuning | A leaderboard does not establish local memory fit or quality after quantization. | Record model/digest and requested settings; do not infer GPU performance. Controlled cold/warm and memory trials remain needed. |
| Per-PC calibration | A good profile on one machine may perform differently on another. | Manual trial/checklist now; automatic tuning, persistent per-device profiles and hardware/runtime identity enforcement are planned in per-pc-calibration.md. |
| Visual/accessibility checks | Working APIs do not establish usable desktop or phone controls. | Limited historical Chrome checks are recorded in design-qa.md. Fresh browser navigation failed in the control layer during the current review; this build has no new visual/accessibility acceptance. Wider device and assistive-technology qualification remains open. |
| Setup boundaries | Defaults can expose source or imply an unproven model won. | Loopback app, metadata-first checks, explicit roots and unqualified labels. A supported-Python source launcher and persisted service AI choice now exist. Windows, guided source setup and automatic downloads remain pending. |
| Sensitive data | Exact evidence can contain private material. | No automatic cloud client; copy/export is explicit. Owners choose permitted roots. Complete secret detection and daemon network isolation are not provided. |
| Licensing and updates | Terms, candidate tags and benchmark conditions change. | Keep publisher links separate from local results; recheck licenses/tags before shipping downloads. No universal best-model or free-compute claim. |
| Review provenance | An edited review record does not prove correctness. | Policies outside inspected roots; matching records required. Review identity is self-asserted. Authenticated independent promotion remains future work. |

The next useful experiment is completion of the existing screening reviews, followed by one actual host handoff and a frozen unseen paired comparison. Existing screening failures must stay visible. The helper remains preparation for the main assistant's reasoning; no deployment or production-readiness claim follows from these checks.
