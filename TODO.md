# Shake and Bake: prioritized to-do list

Updated November 5, 2026 for `0.4.0.dev8`. The current build has 171 passing offline program tests. New owner-PC screening includes a retained Qwen 3.5 4B timeout and an unblinded assistant review of Qwen 3 1.7B: 4 of 10 exposed handoffs met the disclosed rubric. A follow-up prompt experiment remained at 4/10 with more unsupported claims, so its prompt was reverted; only the pre-source thinking-mode compatibility guard ships. See docs/screening-2026-11-05.md and docs/validation-0.4.0.dev8.md. Original `.dev6` reviews, independent/unseen accuracy, broader host qualification and savings remain open. Accuracy takes priority over speed or smaller prompts.

Cross-cutting product priority: connect setup, local preparation, evidence review, host handoff and recovery into one understandable experience. `docs/UX-WORKFLOW.md` specifies the target journey, shared-state gap and implementation slices. This work proceeds alongside accuracy qualification.

## Next qualification steps

- [ ] **1. Complete actual-PC/model qualification (partial).** Run the startup/GUI checks, inspect trusted cloud-disabled Ollama, and record actual CPU/GPU/RAM, OS/runtime versions, exact model digest and quantization. Mark unknown hardware values explicitly. Complete when the real-machine readiness report and selected installed-model identity are recorded. Use `docs/PC-CHECKLIST.md`.

- [ ] **2. Improve and review real Ollama screening (partial).** The missing `.dev6` folders remain unscored; new runs do not reconstruct them. Fresh owner-PC trials are captured and reviewed in docs/screening-2026-11-05.md: Qwen 3.5 4B stopped after a timeout; Qwen 3 1.7B completed ten cases but met the assistant-review rubric on only four. Source coverage passed, but decisive misses and unsupported claims keep profiles unqualified. The follow-up prompt experiment did not improve the 4/10 result and was rejected; the new compatibility guard prevents knowingly incompatible thinking requests. Preserve these records and failures; find a stronger eligible candidate or a preparation task design that meets exposed checks before unseen qualification. Independent review and original receipt recovery remain open. See `docs/pc-readiness-and-trials.md` and ACC-01.

- [ ] **3. Qualify real host delegation (partial).** Installed SDK 2.3.0 stdio/shared checks and actual Codex synthetic handoff/cancellation checks passed; see docs/codex-host-handoff.md. Exact task/source, refused project access, paused AI and completed-job cancellation were verified. A follow-up explicitly stopped one owned preparation runner: Codex observed RUNNING/busy, cancelled it, was refused cancelled evidence, then completed a fresh task. Timeout/disconnect/restart, cancellation during actual model work and local-model orchestration remain pending. Claude Code was signed out; qualify it when authenticated and qualify consumer ChatGPT separately. Complete when each supported host can delegate, retrieve exact evidence, receive uncertainties and handle failure/cancellation without an unsupported final-answer claim. These synthetic checks do not close INT-01 or qualify private source.

- [ ] **4. Compare correctness on unseen tasks.** External dataset loading, input identity checks and separate review are now implemented; see docs/held-out-evaluation.md. Freeze genuinely unseen defective and clean cases outside tuning inputs. Compare the same native host/settings with deterministic evidence and local-model-assisted evidence; assess final task outcomes, critical misses, unsupported claims and useful abstention. Complete when reviewed, comparable records meet the native baseline and existing critical-error/identity gates. Repeated known cases are not independent evidence or promotion authority.

- [ ] **5. Measure the whole-task benefit.** Include local preparation, host/tool descriptions, evidence follow-ups, retries, failures, correction time and available cached/uncached usage. Complete when accuracy, elapsed time and actual provider usage can be compared per successful task. Keep unavailable usage/savings unknown; do not convert prompt shrinkage into a subscription-quota promise. See MET-01.

## Product and release work

- [ ] **6. Build per-PC calibration and profile storage.** Detect supported capabilities, bound time/memory, compare candidates/settings, persist versioned profiles and invalidate them after relevant model/runtime/hardware/settings changes. Complete when identity enforcement, held-out review and safe fallback work on real machines. Current trials support manual screening; automatic tuning remains planned. See CAL-01 and `docs/per-pc-calibration.md`.

- [ ] **7. Connect and verify the whole user journey (partial).** The source launcher selects supported Python and Local AI on/off now persists across restart. Guided source setup, durable jobs and profile persistence remain open. Follow `docs/UX-WORKFLOW.md`: shared GUI/adapter job-policy-pause semantics, guided first run, clearly pinned results, actionable recovery and honest assistant handoff. Build the planned tuning/license views from actual records. Complete when real task walkthroughs and desktop/phone/keyboard/reduced-motion checks pass, with measured/unknown/published/local results distinct. See UX-01, UI-01 and `docs/per-pc-calibration-ui.md`.

- [ ] **8. Qualify secret/private-data handling.** Define permitted handling in ordinary files, captured evidence, logs, exports and host handoffs; test the chosen block/preview/redaction behavior without silently altering exact evidence or hiding gaps. Complete when those cases are verified before sensitive-source handoff qualification. Filename exclusions alone do not close SEC-01.

- [ ] **9. Complete security, dependency and license review.** Independently review boundaries, broaden hostile-input/sustained-load checks, pin actual dependency/model artifacts and retain their required notices. Complete when applicable findings and distribution gaps have recorded dispositions and no release blocker remains for the promoted feature. The tested connection cases do not close the wider audit. See SEC-02–SEC-06, LIC-01, `KNOWN_ISSUES.md` and `docs/LICENSING.md`.

- [ ] **10. Prove recovery and package support.** Exercise unavailable models, timeouts, cancellation, source/model changes, restart, cold/warm behavior and measured memory on target PCs. Implement durable recovery/profile persistence where promised; document safe setup, update, rollback and uninstall. Complete when the actual package preserves user projects/data and supported workflows survive the stated failure cases. Linux is the current development target; Windows needs its own equivalent read/process boundary and qualification before support. See REL-01 and PLAT-01.

Steps 1–2 require the actual local model/PC. Host-dependent steps need the supported client and account. Profile/UI/security development can proceed separately, while their real-machine and qualification checks remain open. Do not treat a pending item as completed because another layer passed tests.

## Evidence already available

- Standalone source package with self-contained synthetic fixtures.
- Evidence collector, optional bounded Ollama transport, local interface and recorded demo preview.
- Startup diagnostics, checkpointed trial capture and separate review scoring.
- New owner-PC exposed screening with a retained timeout, ten reviewed smaller-model notes and a checksummed portable review packet; no model promotion.
- Tested pre-source thinking-mode refusal with exact evidence retained; rejected prompt experiment and portable comparison records.
- Shared local GUI/adapter jobs, routed policy, scoped project access and session pause/cancel verified through native clients.
- Selected local connection/queued-expiry regressions; 171 offline program tests passed in the development environment.
- Actual Codex evidence-only synthetic handoff and injected cancellation/recovery, with opt-in replay and sanitized receipts; full host qualification remains open.
- PC checklist, Known Issues/release rules, licensing inventory and per-PC GUI/calibration specifications.

Keep `KNOWN_ISSUES.md` as the issue-status record and `docs/PC-CHECKLIST.md` as the detailed real-machine runbook. Mark items complete only with the relevant recorded evidence.
