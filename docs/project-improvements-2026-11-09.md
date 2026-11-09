# Project improvement pass — November 9, 2026

This pass improves the existing local evidence-preparation workbench. It keeps
the owner's [standalone, read-only direction](planning/source-record.md), exact
requests and source, optional local AI, and manual assistant handoff.

## Changes in this pass

| Area | Problem addressed | Change |
| --- | --- | --- |
| First use | Setup, privacy and recovery instructions were spread across detailed records. | [Your first useful brief](quickstart.md) gives one path through the synthetic demo, source review, copy and explicit project configuration. |
| Draft privacy | Task text was saved automatically with no in-app opt-out or clear action. | [Draft privacy controls](draft-privacy.md) allow page-only drafting and clearing, preserve captured briefs, and respect another tab's opt-out. Storage failures are visible. |
| Source handling | Non-UTF-8 Linux filenames could break a whole job; escaped valid text could exceed the runner's smaller serialized result limit. | [Source and transport fixes](source-boundary-reliability.md) disclose unusable filenames, validate request encoding, and keep bounded result limits consistent. Exact text is retained. |
| Source display | The browser used different line boundaries from the collector. | The source view follows the collector's line boundaries, including CR-only and Unicode separators, while copy/export retains the original text. |
| Evaluation | The public host runner produced review sheets without a receipt-bound scorer. | [Offline host review](host-review-scoring.md) binds judgments to exact recorded answers, rejects changed identities and inconsistent reviews, preserves failures and missing measurements, and labels reviewer declarations. |

These are development changes. The change-review candidate remains outside
normal GUI, CLI and MCP routing. No new model or host inference is required for
these improvements, and no inspected project is executed or modified.

## Product priorities after this pass

| Order | Outcome | Completion evidence still needed |
| --- | --- | --- |
| Next | Establish one useful preparation workflow. | Redesign on development material, freeze the candidate, then compare fresh permitted tasks with equal native source/tool access. Review complete answers, failures, follow-up and correction work; obtain separate human review. |
| Next | Make real-project setup understandable. | An owner-controlled source approval flow and returning-user walkthrough that preserve root permissions, draft identity and explicit sharing decisions. The new guide helps; guided setup remains open. |
| Next | Define private-source handling. | Explicit rules and verified block/preview behavior for ordinary files, evidence and exports. Draft controls do not establish secret detection or secure cloud handoff. |
| Later | Persist jobs and qualified profiles safely. | Versioned atomic storage, source/model/runtime identity invalidation, bounded recovery and actual-PC interruption checks. A saved browser draft is not durable job recovery. |
| Later | Extend platforms and connected delivery. | Separate filesystem/process boundaries, supported-host acceptance and real acknowledgements before claiming support or delivery. |

The [existing TODO](../TODO.md) remains the full qualification queue. This pass
does not close its real-model, native-host, security, accessibility, platform or
whole-task-benefit gates.

## Why reviews retain their limits

SciSpace discovery and primary-paper checks found published evidence of bias in
LLM judges, including position effects and sensitivity across tasks. See
[Justice or Prejudice?](https://arxiv.org/abs/2410.02736) and
[Judging the Judges](https://arxiv.org/abs/2406.07791). These studies support
keeping machine-generated judgments visibly separate from human review; they
do not measure this project's accuracy. An entered reviewer name or `human`
label is self-declared, and answer hashes establish byte identity, not truth.

## Validation record

The isolated starting snapshot passed **191 offline program tests** on Python
3.12. Synthetic selection, evidence-only Task Lab, interface syntax and the
existing lightweight JavaScript checks also passed before the changes.

| Check | Result | What it establishes |
| --- | --- | --- |
| Python 3.12 source suite | 223 passed | Existing contracts plus sixteen source/transport and sixteen host-review regressions. |
| Python 3.14 source suite | 223 passed | The same program checks on the launcher's newer installed interpreter. |
| Isolated Python 3.12 installed wheel | 223 passed; installed demo/shared/preference smoke passed | Installed package behavior on synthetic fixtures, including exact source retrieval and saved Local AI off across restart. |
| Source browser checks | 41 workbench + 14 readiness + 5 clipboard scenarios passed | Actual Chromium DOM/events, synthetic source, simulated readiness/failure responses, draft/privacy races and copy recovery. |
| Installed browser checks | The same 60 scenarios passed | Those browser contracts against the isolated installed package. |
| Lightweight JavaScript checks | API smoke and 59 checks passed; syntax valid | File-launch behavior, model-state races, clipboard, server startup and request deadlines. |
| Synthetic selection and evidence-only Task Lab | Both selection variants and all ten Task Lab cases passed | Expected exact source spans and mechanical evidence integrity on exposed synthetic cases. |
| Offline host-review CLI | Prepare/score passed with a blank synthetic review | Pending values remain unknown, promotion stays disabled and new outputs are owner-only. |
| Wheel inspection | Source/assets/notices match byte for byte; no core runtime dependencies | The built package contains current code and web assets, including the final retention reminder. |
| Preservation and diff checks | All twenty preexisting changed/new original files retain their initial hashes; whitespace checks pass | The original checkout remains intact while this separate copy carries improvements. |

The browser checks used existing Chrome 157 and isolated profiles. The final
static retention reminder was followed by relevant GUI checks, wheel byte
verification and source/installed workbench reruns. Desktop and 390-pixel phone
captures were inspected for the new controls; wider-device and formal
accessibility qualification remain open.

The new scorer was checked with synthetic receipts only. Existing public trials
were not regraded, and no model, cloud host or private-project workflow was activated by this pass. The optional official
MCP SDK/real-host checks were not rerun; no MCP tool contract changed. All
changes remain local and uncommitted; no push, merge, deployment or publication
was performed.

Synthetic fixtures and simulated service responses establish only the stated
contracts. Real model accuracy, independent security qualification and
whole-task savings remain unmeasured by this pass.
