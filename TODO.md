Current development update (November 5): `0.4.0.dev6` adds explicit computer/model readiness, exact shared wire/receipt settings, per-call runtime guards and worker-visible collection limits. The suite passes 140 tests. Two ten-case exposed real-model screenings completed structurally, but confirmed reasoning errors keep the model unqualified. Full calibration/profile binding, durable recovery, unseen native-host comparison and broader gates below remain open. See docs/validation-0.4.0.dev6.md.

# Shake and Bake: prioritized to-do list

Updated November 4, 2026. All items below are pending. The current development build has 121 passing program tests; real-model accuracy, actual host connections and cloud savings remain unmeasured. Accuracy takes priority over speed or smaller prompts.

Cross-cutting product priority: connect setup, local preparation, evidence review, host handoff and recovery into one understandable experience. `docs/UX-WORKFLOW.md` specifies the target journey, shared-state gap and implementation slices. This work proceeds alongside accuracy qualification.

## Next qualification steps

- [ ] **1. Verify the actual PC and installed local model.** Run the startup/GUI checks, inspect trusted cloud-disabled Ollama, and record actual CPU/GPU/RAM, OS/runtime versions, exact model digest and quantization. Mark unknown hardware values explicitly. Complete when the real-machine readiness report and selected installed-model identity are recorded. Use `docs/PC-CHECKLIST.md`.

- [ ] **2. Run and review a real Ollama trial.** Start with one inert synthetic case, then the full exposed Task Lab and repeated runs. Keep exact source, output, settings, failures, time and available usage. Complete when actual model handoffs have a separate evidence-backed review; a completed run or valid JSON is insufficient. This is development screening, not held-out qualification. See `docs/pc-readiness-and-trials.md` and ACC-01.

- [ ] **3. Qualify real host delegation.** Run the optional shared-path SDK smoke check (`integration/mcp_shared_smoke.py`), then a supported Claude Code handoff; qualify ChatGPT separately. Native shared-coordinator tests now cover common jobs/policy/pause but do not complete these host gates. Use inert/permitted source first. Complete when each supported host can delegate, retrieve exact evidence, receive uncertainties and handle failure/cancellation without an unsupported final-answer claim. Prepared adapters alone do not complete INT-01.

- [ ] **4. Compare correctness on unseen tasks.** Freeze unseen defective and clean cases outside tuning inputs. Compare the same native host/settings with deterministic evidence and local-model-assisted evidence; assess final task outcomes, critical misses, unsupported claims and useful abstention. Complete when reviewed, comparable records meet the native baseline and existing critical-error/identity gates. Repeated known cases are not independent evidence or promotion authority.

- [ ] **5. Measure the whole-task benefit.** Include local preparation, host/tool descriptions, evidence follow-ups, retries, failures, correction time and available cached/uncached usage. Complete when accuracy, elapsed time and actual provider usage can be compared per successful task. Keep unavailable usage/savings unknown; do not convert prompt shrinkage into a subscription-quota promise. See MET-01.

## Product and release work

- [ ] **6. Build per-PC calibration and profile storage.** Detect supported capabilities, bound time/memory, compare candidates/settings, persist versioned profiles and invalidate them after relevant model/runtime/hardware/settings changes. Complete when identity enforcement, held-out review and safe fallback work on real machines. Current trials support manual screening; automatic tuning remains planned. See CAL-01 and `docs/per-pc-calibration.md`.

- [ ] **7. Connect and verify the whole user journey.** Follow `docs/UX-WORKFLOW.md`: shared GUI/adapter job-policy-pause semantics, guided first run, clearly pinned results, actionable recovery and honest assistant handoff. Build the planned tuning/license views from actual records. Complete when real task walkthroughs and desktop/phone/keyboard/reduced-motion checks pass, with measured/unknown/published/local results distinct. See UX-01, UI-01 and `docs/per-pc-calibration-ui.md`.

- [ ] **8. Qualify secret/private-data handling.** Define permitted handling in ordinary files, captured evidence, logs, exports and host handoffs; test the chosen block/preview/redaction behavior without silently altering exact evidence or hiding gaps. Complete when those cases are verified before sensitive-source handoff qualification. Filename exclusions alone do not close SEC-01.

- [ ] **9. Complete security, dependency and license review.** Independently review boundaries, broaden hostile-input/sustained-load checks, pin actual dependency/model artifacts and retain their required notices. Complete when applicable findings and distribution gaps have recorded dispositions and no release blocker remains for the promoted feature. The tested connection cases do not close the wider audit. See SEC-02–SEC-06, LIC-01, `KNOWN_ISSUES.md` and `docs/LICENSING.md`.

- [ ] **10. Prove recovery and package support.** Exercise unavailable models, timeouts, cancellation, source/model changes, restart, cold/warm behavior and measured memory on target PCs. Implement durable recovery/profile persistence where promised; document safe setup, update, rollback and uninstall. Complete when the actual package preserves user projects/data and supported workflows survive the stated failure cases. Linux is the current development target; Windows needs its own equivalent read/process boundary and qualification before support. See REL-01 and PLAT-01.

Steps 1–2 require the actual local model/PC. Host-dependent steps need the supported client and account. Profile/UI/security development can proceed separately, while their real-machine and qualification checks remain open. Do not treat a pending item as completed because another layer passed tests.

## Evidence already available

- Standalone source package with self-contained synthetic fixtures.
- Evidence collector, optional bounded Ollama transport, local interface and recorded demo preview.
- Startup diagnostics, checkpointed trial capture and separate review scoring.
- Shared local GUI/adapter jobs, routed policy, scoped project access and session pause/cancel verified through native clients.
- Selected local connection/queued-expiry regressions; 121 program tests passed in the development environment.
- PC checklist, Known Issues/release rules, licensing inventory and per-PC GUI/calibration specifications.

Keep `KNOWN_ISSUES.md` as the issue-status record and `docs/PC-CHECKLIST.md` as the detailed real-machine runbook. Mark items complete only with the relevant recorded evidence.
