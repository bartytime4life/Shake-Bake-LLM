# Documentation reconciliation

November 11, 2026 (Chicago). The audit-start GitHub readback was November 12 at 01:25 UTC. This is a documentation/source-integration record, not a new model, host or usability experiment.

## What changed

Active user guides, architecture/helper/shared/API contracts, evaluation/setup instructions, development commands and design plans are reconciled with the reviewed dev37 source. The [documentation guide](README.md) points to maintained instructions; the [catalog](catalog.md) inventories current references, plans, research, historical evidence and fixed inputs. [Current status](current-status.md) centralizes source/delivery identity and the scope of the 516 Python / 134 browser / 75 JavaScript baseline, rather than copying old counts into new claims.

Corrections include the actual job-first workflow/disclosure labels, source preparation across workflows, retained failed-run JSON versus guarded handoff, truthful history outcomes, current collection/transport limits, 1,024 requested worker output tokens, shared routed MCP behavior and installation checks that work from a checkout path containing spaces. Planned calibration/profile/dashboard work remains planned.

No original request, fixture, source/demo packet, recorded model answer, import checksum or historical experiment is rewritten. Dated research/license observations retain their checked dates. Documents mixing current procedure with historical evidence keep those parts explicitly separate.

## Integration observation

At the start of this audit, `origin/main` was `fc639f0` (dev36, PR #71). PR #72 had merged dev37 into the former feature branch after that main merge, so its closed/merged status did not establish delivery to main. This branch integrates the exact reviewed recovery tree from `3e59075` as `62c6fef`, with both reviewed source and main as parents, then adds documentation changes for review to main. The connected GitHub integration delivers these objects after the local Git credentials refused a push; remote/local tree identity is verified separately. Runtime, scripts, tests, policies and package version are unchanged from the reviewed recovery source; this pass does not introduce a second implementation.

The original working checkout and owner installation remain unchanged. Any subsequent merge, CI result or installation must be read separately from the live PR; the observations above are dated, not a promise about future branch state.

## Verification

The final local checks on this documentation branch passed:

| Check | Result and scope |
| --- | --- |
| Catalog coverage | All 127 tracked/new documentation and text files are classified; generated/ignored local files are excluded. |
| Local documentation links | 701 relative links and fragments resolve, with no missing targets or headings. External URLs were not revalidated. |
| Examples | 35 Bash blocks in current guides/plans pass `bash -n`; all four JSON examples parse. Syntax checks alone do not execute every example. CLI flags and displayed workflow labels were also checked against source/help. |
| Preservation | 187 historical, research, original, fixture, receipt, import and legal-input files match the reviewed `3e59075` bytes. Historical sections retained within updated current guides were reviewed separately. |
| Runtime identity | Runtime, scripts, tests, integration checks, requirements and package version match reviewed dev37. |
| Python | 516 tests pass on Python 3.12 from source and another 516 pass from a fresh installed wheel outside the checkout with `PYTHONPATH` unset; the installed import resolves inside that environment. |
| JavaScript | 39 clipboard/activity, 30 model-readiness and six request-deadline checks pass. |
| Package | A fresh wheel passes the code/assets/legal verifier. Its README metadata also matches the current root README bytes. Installed demo/shared-state, private Local AI retention and doctor checks pass without a model/cloud call. |
| Official SDK | Hash-locked SDK 2.3.0 passes installed stdio subprocess, shared-service and in-process checks outside the checkout with `PYTHONPATH` unset. |

The rebuilt `shake_and_bake_assistant-0.4.0.dev37-py3-none-any.whl` has SHA-256
`34d0e74ea2b9a2fa01797cdbe0b3444d5baae888fbb5e46b92ca397c70c4e964`.
The root README changes its metadata; this is distinct from the prior dev37
artifact retained in the recovery record. The build and isolated test environments
are local, ignored artifacts and are not committed or installed over the owner's app.

The 134-scenario source/installed browser result in current status is the earlier
reviewed runtime baseline; this local documentation pass did not rerun that browser
suite. Hosted checks and PR delivery state are reported on the PR so a later event
cannot silently rewrite earlier evidence. No model/host experiment, independent
human grade, upstream research refresh or owner-PC acceptance was performed here.
