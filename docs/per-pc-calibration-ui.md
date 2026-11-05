# Your computer & tuning: GUI plan

Status: planned for a future interface milestone. The current visual workbench has model explanations and evidence views; it does not yet provide hardware detection, automatic calibration or a saved per-PC tuning dashboard. The doctor command supplies limited readiness information now.

## Make the computer's state visible

Add **Your computer & tuning** to navigation and link to it from each model's expanded details. The first visit offers a guided check. Returning users see their current local profile and whether it still matches this machine/model/runtime. Model names and technical settings stay expandable; the main task interface retains the goal-first choice and Best accuracy default.

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

The existing model panel should gain a **This PC** subsection: installed digest/quantization, hardware/runtime used, context/output/thinking options, task category, evaluation date and cohort, unique case and attempt counts, reviewed correctness, measured timing/memory, failures, limits and a Retest link. A separate **Publisher results** subsection retains the official benchmark links and reported settings. A third **Why selected** subsection names the actual gates and tie-breaks used.

Actual timing and memory should use compact comparison bars or plots only when measured. Show exact values in adjacent text/table cells so color, animation or chart interpretation is not required. Progress animation has reduced-motion behavior; status changes use accessible announcements, keyboard focus and plain text. The layout must work on desktop and a narrow phone view.

## Acceptance checklist for this GUI milestone

- [ ] Every metric has an origin, unit, date and clear measured/estimated/unknown label.
- [ ] Zero completed tests cannot render a qualified or recommended winner.
- [ ] Hardware/model/runtime/settings changes visibly stale the profile before automatic selection.
- [ ] Stop, restart and interruption preserve honest completed/failed attempt counts.
- [ ] The same task/accuracy gates apply across computers, including CPU-only and lower-memory machines.
- [ ] Override/download controls explain the action without silently weakening accuracy requirements.
- [ ] Publisher statistics and this-PC measurements remain separate in cards, details, charts and exports.
- [ ] Desktop, phone, keyboard and reduced-motion behavior are actually reviewed before GUI qualification.

This is the next design target, not a claim that those controls already work. Implementation depends on capability detection, a versioned local profile store, selector identity enforcement and a bounded calibration/review flow described in per-pc-calibration.md.
