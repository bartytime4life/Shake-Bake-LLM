# Workbench and Ollama validation — November 5, 2026

This record covers this repository's `0.2.0.dev0` candidate. It does not claim parity with the separate historical archive in the Drive plan.

## Executed checks

- The source suite passes 66 tests on Python 3.14.4. It includes exact evidence and source limits, lexical no-match/distant-window behavior, v1 store upgrade without receipt loss, profile gates, no calls when off/unqualified, model identity changes before/after inference, remote metadata, duplicate/unknown citations, malformed/incomplete replies, chunked responses, response flooding, redirects, cancellation/pause, persistent model choice and private demo-copy handling.
- Real HTTP tests exercise browser authorization, exact Host/Origin/CSRF, scoped jobs, unavailable root/configuration mutation, private native authentication/scope, handler capacity, incomplete authenticated bodies and absolute slow-header expiry. These are bounded program checks, not complete flood resistance or independent security qualification.
- A clean installed-wheel environment runs the same suite without checkout `PYTHONPATH`. The official SDK 2.3.0 subprocess check exercises the four tools; a separate installed GUI/native replay verifies shared jobs/evidence, cross-entry pause, continued service access after client close and private publication cleanup.
- Wheel inspection compares all GUI assets, icon notice, application notices and inert fixture bytes against source. JavaScript syntax is checked with Node; Node is not an app runtime dependency.
- Actual Chrome desktop/phone interaction and comparison evidence is recorded in [design-qa.md](../design-qa.md). The JSON download was read back against its pinned synthetic job. Original request and exact source remain included in copy/export.

The installed replay exposed package-manager hard links in bundled fixtures. The fix creates private single-link demo copies, retains root-policy restrictions and preserves/refuses owner-modified demo files. Both the boundary regression and the installed shared replay cover this behavior.

## Real local-model observations

Only bundled synthetic source was submitted. No model was downloaded, daemon started, global service stopped, host configuration installed, private project source sent or paid provider called.

The actual local inventory reported three installed candidates. A Qwen 2.5 7B attempt reached the configured 30-second deadline, discarded its note and retained the exact source. An installed Qwen 3 4B model exposed older runtime thinking metadata; the client now requests documented `think: false`, rejects explicit incompatible metadata and rejects any returned thinking output.

After that compatibility fix, `qwen3:4b-instruct-2507-q4_K_M`, reported digest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`, completed one synthetic trial. Receipt: 24.635762 seconds, two exact source ranges/344 excerpt bytes, one model call/six local HTTP requests, 882 reported prompt tokens and 326 reported output tokens. Cloud calls were zero; cloud token savings remain unknown. Job identity and full synthetic receipt remain private local test artifacts.

The note passed schema and evidence-ID checks, but one uncertainty incorrectly said supplied line 2 was absent. That contradiction is preserved, not silently corrected or promoted into a fact. This is evidence for keeping candidate notes unverified, not qualification of model accuracy, hardware performance or a preferred model. No held-out final-task comparison or native-host baseline ran.

## Remaining gates

Actual model/task qualification, complete hardware/runtime calibration, actual Claude/ChatGPT host UX, broader secret/private-data handling, independent security/dependency/license qualification, sustained load, Windows equivalence and full-workflow savings remain open. Owner profile records are declarations rather than authenticated test certificates. Closing the client does not prove the Ollama daemon stopped GPU work.

Hosted CI status is separate from these local observations and must be read from the run associated with the pushed commit.
