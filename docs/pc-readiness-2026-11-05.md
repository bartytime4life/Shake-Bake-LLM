# Local PC readiness walkthrough — November 5, 2026

This check continued from merged commit `7a770bc2ae15d3b18a556082660566c101ba46f8`
(PR #9). The previously checked-out worker branch was clean and preserved; the
follow-up uses a new branch. No model inference or cloud-host task ran.

## Package and machine identity

The checked checkout contains PR #8. Its original interface SHA-256 was
`8fabff47c2707f82d1958ef158e5dc73aaca66aead508413caa1cfc359c0d2bf`.
An isolated Python 3.12 installation outside the checkout imported the installed
package, matched that interface, and passed startup and shared-controller checks.
All 33 packaged code/assets and three legal files matched the selected source.
The existing build output and previous trials were preserved.

CPU, RAM, operating system, GPU/driver observations, UTC times, command statuses,
installed paths and model metadata are retained in a private local acceptance
record. A separate `nvidia-smi` observation supplied NVIDIA memory information
that the app's sysfs probe did not detect; the UI correctly left that value
unknown. Neither observation measures model fit, peak memory or throughput.

The selected installed `qwen3:8b` reported digest
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`,
Ollama `0.35.1`, Q4_K_M quantization, 8.2B parameters and support for disabling
thinking. Metadata remained stable during the check. It is still unqualified.

The shared daemon's startup record reported cloud disabling **false**. Only
inventory/version/model metadata was requested from it. The daemon was not
restarted or reconfigured, no model was loaded/downloaded, and no source was
sent to it. Use a separately verified cloud-disabled daemon before an inference
trial. The earlier model reasoning failures remain open.

## Browser observations

Chrome automation could create blank tabs but its navigation API failed. The
local in-app browser reached the actual installed loopback workbench and was
used for these observations. These are not new Chrome acceptance results.

| Check | Observed result |
| --- | --- |
| Fresh isolated settings | Local AI starts off; only the bundled synthetic demo is approved. Candidate generation is disabled by launch configuration. |
| Prepare the bundled demo | Two exact excerpts and their hashes are visible. Original request/job identity is pinned; the result says diagnosis remains open. |
| Local AI off | Inventory action reports that no request was made; model-check control is disabled. |
| Explicit installed-model check | The UI reports the selected digest, quantization, runtime and check time, separately from computer observations and unmeasured accuracy. |
| Refresh unchanged inventory | Previous facts disappear and the selected name/digest remains pinned. An explicit recheck restores facts. |
| Change away and back | Selecting Qwen 3 1.7B clears the Qwen 3 8B facts; returning to 8B does not revive them. |
| Local AI off/on | Old facts stay cleared. The isolated session was returned to off. |
| Narrow layout and keyboard | At a 390 × 844 viewport there was no document-level horizontal overflow; keyboard Tab reached the prepare action with visible focus. This is a bounded walkthrough, not an assistive-technology audit. |
| Reduced motion | With the browser media override set to reduce, the prepare button had zero transition duration. The override and viewport were reset. |
| Download JSON | The synthetic export retains the exact request, both excerpts and hashes, null model notes and `final_answer_ready=false`. |
| Clipboard copy | Clicking Copy did not yield confirmed clipboard text or a success/error message in this browser. Copy remains unverified here; the successful JSON export is a separate result. |

No real installed model disappeared or changed digest during this walkthrough.
Pending-response replacement/removal, unavailable inventory and stale failure
handling retain their earlier **synthetic** regression/CI evidence; those real-PC
scenarios are not marked complete. No weights or shared services were changed to
manufacture those situations.

## Refresh status correction

The real walkthrough exposed a status defect: after an unchanged inventory
refresh completed, model facts were correctly cleared but the readiness text
still said “Refreshing inventory.” The interface now explicitly reports
“Inventory refreshed” and asks for another model check. Error handling, exact
selection pins, metadata invalidation and generation permissions are unchanged.

Existing deterministic refresh cases now check both pending and completed
status. Before the fix, four of the 30 cases failed; afterward all 30 pass.
The candidate interface SHA-256 is
`0a6acc8693659a1eadbc94c32e1f99e5f7e001dd15f2ecba1a6d27f17b1addb7`.
The package version remains `0.4.0.dev8`, so use the interface/artifact identity,
not that version alone, to identify this correction.

All 176 source tests pass on this PC with Python 3.12.3, including the real
owned-runner process-gate test with no skips. Both the original and corrected
isolated installed packages also passed all 176 tests, unlike the
namespace-limited development environment recorded in the earlier follow-up.
The corrected installed interface passes all 30 readiness regressions. The
installed shared-controller/demo and preference-restart smoke checks pass too.
These results do not extend the actual cloud-host cancellation receipts or prove
cancellation of GPU work. No MCP implementation changed; the earlier SDK checks
retain their original scope.

The corrected wheel was built offline with setuptools 78.1.1 and wheel 0.46.3;
all package assets and legal-file bytes were verified again. Its installed
interface matches the candidate hash above. After shutting down the first
workbench, the doctor's bind probe for port 8421 failed even though a subsequent
listener check was empty. That failed result is preserved. The documented
alternate-port path passed on 8422, where the corrected installed workbench
opened with the saved Local AI off setting and empty session-only job history.

In that final installed browser session, a real Qwen 3 8B metadata check followed
by an unchanged-inventory refresh showed the new completion text, cleared model
facts and preserved the explicit digest pin. Local AI was returned to off.

Private raw records and build artifacts are excluded from Git. Only this scoped
summary and synthetic regression changes are part of the source change. The PC
checklist, UI-01, ACC-01, host qualification and whole-task savings stay open where
their required evidence remains missing.
