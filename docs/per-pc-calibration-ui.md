# Your computer & tuning: GUI plan

Status refreshed for the reviewed `0.4.0.dev37` source. [Current status](current-status.md) separates source, validation and delivery; [the workbench guide](visual-workbench.md) describes active controls. The full navigation/dashboard, automatic calibration, durable test recovery, comparisons and saved per-PC profiles below remain planned. Historical model/candidate observations and trials remain in [evaluation status](evaluation-status.md); this documentation audit adds no research, recommendation or tuning controls.

The implemented subset is **Options → Model details → This computer & selected model**, with explicit **Check this computer** and **Check selected model** metadata actions, detected/unknown values, model/pipeline identity and **Published statistics & local results**. These are readiness facts, not measured fit, task accuracy or an authenticated per-PC profile. Preparation mode waits until initial connection and saved choices are ready; no automatic calibration or model download follows.

The surrounding application already has **Diagnose a failed run** and **Prepare source brief**, explicit session **Connect folder**, actual shared preparation activity, source-draft saving/opt-out/clear, and retained failed-run JSON through failed rechecks. These do not depend on this planned dashboard. The failed-run workflow calls no model; ordinary source preparation remains evidence-only when no profile qualifies. See [dev36 UI scope](workbench-usability-2026-11-11.md) and [dev37 recovery scope](captured-report-recovery-2026-11-11.md).

## Make the computer's state visible

Proposed: add **Your computer & tuning** to navigation and link to it from expanded model details. A future guided first visit would check the installation; returning users would see a saved profile and whether it still matches the machine/model/runtime. Model names and settings would stay expandable, preserving the current job-first task interface. A proposed Best accuracy selector must not be confused with today's **Best tested for this task** owner-policy mode.

| Visible area | Information and visual behavior | Honest empty/failure state |
| --- | --- | --- |
| Your computer | Simple CPU, RAM and GPU/VRAM cards, plus a compact capability graphic. Expand for OS, backend and driver/runtime versions. | Unknown values say Not detected; no hardware or performance is inferred. Distinguish total RAM from the memory actually available. |
| Models that fit | Candidate cards with verified installed status, exact size/quantization and estimated memory fit. Show publisher sources separately. | Estimated fit is not measured fit or qualification. CPU-only systems remain valid candidates for testing. |
| Test this PC | Clear Start, Stop and Resume/restart choices once durable recovery exists. Show the actual case count, current stage and completed attempts. | No invented percentage or ETA; distinguish loading, running, stopped, interrupted and failed. Current session-only GUI does not yet provide this calibration recovery. |
| Results by job | Code, Troubleshoot, Documents and Search cards showing reviewed accuracy, critical misses, unsupported claims, time and measured peak memory. Expand to every attempt and its evidence. | Unreviewed accuracy says Awaiting review. Missing usage stays Unknown. Repetitions and unique cases have separate counts. |
| Recommended for this PC | Highlight a profile only after the applicable review/baseline gates pass. Show the exact task category, model/settings and Why this choice. | No qualifying profile leads to evidence-only preparation with an explanation. An unfinished test does not create a winner. |
| Compare profiles | Side-by-side accuracy and resource measurements for the same evaluation cohort. Charts include units, case counts, settings and dates. | Incomparable hardware/settings/cohorts get an explanation rather than a ranked chart. Published and local results never share an unlabeled score axis. |
| Profile health | Small status card showing matching identities and last successful review. Offer Retest after a material change. | Stale, unqualified, unavailable and not-yet-reviewed are distinct labeled states, not just colors. |

## Guided flow

1. **Check my computer.** Explain what will be read locally; show detected and unknown capabilities. Do not display serial numbers or other unnecessary device identifiers.
2. **Choose candidates.** Offer a small hardware-appropriate set. Already installed models are distinguished from models needing a download; show size/terms and require an explicit download choice. No silent downloads or remote model substitution.
3. **Run a small test.** Explain the time/memory bounds and stop control. Record requested settings and actual failures. Keep the original evidence visible.
4. **Review accuracy.** Show supported results, omissions, contradictions and useful unknowns with source receipts. Exposed development checks remain distinct from unseen qualification and native-host comparison.
5. **Save a local profile.** Show what passed, what remains unknown and the exact task categories allowed. Explain that the profile belongs to this installation and needs re-testing after material changes.

## Expandable model details

Add a separate **License & source** disclosure with upstream license name/link, exact artifact review status, source/quantization/digest, required notices and checked date. Show relevant terms and size before a future explicit download choice. An **About/Licenses** view should expose the app LICENSE and shipped third-party notices. These controls remain planned; upstream observations are currently in MODEL_LICENSES.json.

Beyond the current metadata subsection, the proposed **This PC** profile view would combine installed digest/quantization, hardware/runtime used, context/output/thinking options, task category, evaluation date/cohort, unique case and attempt counts, reviewed correctness, measured timing/memory, failures, limits and Retest. Separate **Publisher results** and **Why selected** sections would retain official links/reported settings and name actual selection gates/tie-breaks. Existing owner declarations and readiness metadata do not supply all these measured fields.

Actual timing and memory should use comparison bars or plots only when measured. Show exact values in adjacent text/table cells so color, animation or chart interpretation is not required. The current source-job activity reports starting, preparing or unknown state; granular loading/gathering/model stages require future backend events. Any proposed calibration progress must report actual attempts/cases with reduced-motion behavior, accessible announcements, keyboard focus and plain text. Desktop/narrow-phone checks remain part of qualification, not an inference from the design.

The source collector's limit is up to ten records: four primary plus six controlling-context records, reduced by other budgets as needed. [Optional embedding reranking](embedding-rerank-2026-11-07.md) is implemented for explicit CLI/benchmark use and remains off by default. Neither mechanism is an automatic calibration/profile dashboard or evidence of semantic accuracy. Connected cloud Send/acknowledgement controls remain separate planned work; manual copy/export is the implemented handoff.

## Acceptance checklist for this GUI milestone

- [ ] Every metric has an origin, unit, date and clear measured/estimated/unknown label.
- [ ] Zero completed tests cannot render a qualified or recommended winner.
- [ ] Hardware/model/runtime/settings changes visibly stale the profile before automatic selection.
- [ ] Stop, restart and interruption preserve honest completed/failed attempt counts.
- [ ] The same task/accuracy gates apply across computers, including CPU-only and lower-memory machines.
- [ ] Override/download controls explain the action without silently weakening accuracy requirements.
- [ ] Publisher statistics and this-PC measurements remain separate in cards, details, charts and exports.
- [ ] Desktop, phone, keyboard and reduced-motion behavior are actually reviewed before GUI qualification.

This checklist is a proposed dashboard milestone, not a claim that the full controls work. Implementation must build on existing metadata detection and policy identity checks, add a versioned local profile store and full identity enforcement, then provide the bounded calibration/review flow in [per-PC calibration](per-pc-calibration.md). Current synthetic browser/program checks do not close these model, hardware, durability or representative-user gates.
