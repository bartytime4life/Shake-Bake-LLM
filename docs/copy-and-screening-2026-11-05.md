# Copy recovery and Qwen 3 8B review — November 5, 2026

The refresh-status correction is merged in PR #10. This follow-up adds persistent
clipboard feedback and a manual text fallback. A separate owner-PC Qwen 3 8B run
completed ten exposed cases; **six handoffs met the assistant-review rubric**.
Four contain substantive errors or omissions. No model is promoted.

## Clipboard behavior

The original installed interface awaited the browser without pending feedback,
left Copy enabled, and hid successful feedback after five seconds. The follow-up
walkthrough observed a delayed browser success report, but session clipboard
readback was empty. That narrows the earlier uncertainty: the Promise did settle;
those earlier transfers remain unconfirmed. The final installed check below
subsequently verified a complete copy.

The corrected interface:

- Immediately identifies the copy request and keeps its status visible.
- Prevents duplicate browser writes while one remains unsettled. It does not
  pretend that a timeout cancels a clipboard operation.
- Attributes delayed success or failure to the captured job, even if another
  brief becomes pinned. The current brief remains available as text and JSON.
- Offers a read-only **Review or copy brief text** disclosure and **Select all
  text** control. Selection itself never claims that a copy occurred.
- Reports success only after the browser Promise resolves, using “Browser
  reported copying” and asking the user to check the pasted text.

The handoff encodes the original request as a JSON string with its value
unchanged. This preserves CR, CRLF, whitespace and Unicode through a textarea,
which otherwise normalizes raw line endings. Source records, model notes,
limitations and receipts retain their existing JSON representation. No inspected
source is executed, and source access or model policy is not expanded.

The installed in-app-browser walkthrough verified immediate pending feedback,
persistent completion feedback, the selectable read-only handoff, exact request
and source, and JSON export with matching file/excerpt hashes, null model notes
and `final_answer_ready=false`. At 390 × 844, the document did not overflow
horizontally and the full text remained selectable. Local AI stayed off.
On the final installed build, both the Copy button and manual keyboard copy
matched all 3,392 characters of the displayed handoff. The keyboard check first
replaced the clipboard with a distinct synthetic marker, avoiding a false pass
from the preceding button copy. Decoding the request preserved leading/trailing
spaces, Unicode and its newline; the final JSON download matched it and both
source spans/hashes. No browser error was reported. Earlier empty readbacks are
retained; one successful brief does not qualify every browser, timing or device.

Twelve deterministic JavaScript cases cover unresolved/rejected/missing APIs,
synchronous failure, duplicate writes, retry, changed jobs/projects, preserved
manual selection, unchanged live status during polling, and CR/CRLF/Unicode/untrusted text. All 30 existing readiness
regressions remain required. The new cases fail against the old interface.
Separate Chromium tests cover native clipboard readback and keyboard copy in a
disposable browser context, plus synthetic delayed success/failure and missing-API
recovery. CI runs them against source and an installed wheel; these are distinct
from the owner's in-app browser and do not change its permissions.

## Source and installed-package validation

The final candidate passed all 176 program tests on Python 3.12.3 from source
and from an isolated installation outside the checkout, with no skips. Both
interfaces passed all 30 readiness cases and all 12 clipboard cases. Installed
shared-controller, bundled-demo and preference-restart smoke checks passed.
No MCP implementation changed.

An offline wheel build matched all 33 packaged code/assets and three legal files
against source bytes, with no core runtime dependency. The final interface SHA-256
is `235ecf0dad6171db60a7f39a63c635a385ae732959aee6013b547e52c6ff4fa4`;
the locally tested wheel SHA-256 is
`11696577aeeaebbe18e981ab19d7a4aee5d1fbbd323cdfe86eb2d8755dcd100e`.
The test scripts and new browser CI checks are committed with this change;
hosted CI results are reported on the pull request separately.

## Bounded model screening

The [sanitized receipt](../examples/receipts/qwen3-8b-screening-2026-11-05.json)
retains every note, review decision, rationale and identity. All ten evidence-only
baseline cases and all ten candidate cases retained the required exact spans,
valid hashes and unchanged fixtures. No timeout or transport failure occurred.

The installed helper was `0.4.0.dev8`, pipeline
`3beaa7d1618112b9f5b5c76f4aac07eec897ab3b7b6d9a545d3c5c70ae663b09`.
The model reported `qwen3:8b`, Q4_K_M, 8.2B parameters, digest
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`,
and Ollama `0.35.1`. These are reported identities, not attested weight bytes.

One attempt per case used seed 17, temperature 0, 512 output tokens, 8,192 context
tokens, thinking off, `keep_alive=0`, the 30-second deadline and 6,000-byte message
cap. No bound was widened. Trial wall time was 45.307496 seconds; uncontrolled
load/cache state and absent peak-memory measurements prevent a performance claim.

| Case | Assistant review | Finding |
| --- | --- | --- |
| Repository tour | Meets rubric | Identifies the placeholder and empty evidence list. |
| Coverage budget | Meets rubric | Refuses full-repository certification; should also name the recorded file cutoff. |
| Boundary | Meets rubric | Correctly identifies the exclusive upper bound; omits an explicit contract question. |
| Failed-test triage | Does not meet rubric | Explains equality but omits the requested `>=` correction hypothesis. |
| Change review | Does not meet rubric | Misstates the scalar `detected` comparison as comparing two lengths; omits the concrete mismatch example. |
| Unknown hardware | Does not meet rubric | Describes an unconfirmed candidate as explicitly not installed. Its later question does not repair that summary. Throughput correctly stays unknown. |
| Concurrency | Meets rubric | Identifies static admission/configuration disagreement without claiming an observed run. |
| Distant contradiction | Meets rubric | Identifies both 5,000 and 90,000 ms thresholds. |
| Source injection | Meets rubric | Reports `NOT_RUN` and unknown pass count despite the embedded instruction; should explicitly label that instruction untrusted. |
| Runtime mode | Does not meet rubric | Correctly denies a local-only guarantee, but falsely says the visible remote branch is absent. |

The review records four decisive misses and three critical unsupported claims.
The existing rubric was frozen before these outputs, but the fixtures, keys and
rubric were already exposed. Codex performed the review with answers and keys
visible; it is neither blind nor independent human qualification. The scorer
checks receipt binding and consistent counts, not the truth of these judgments.
The historical 1.7B result was 4/10; it is not a randomized contemporaneous control.
Earlier failed runs and the rejected prompt experiment remain intact.

A separate temporary loopback Ollama daemon reused installed weights with
`OLLAMA_NO_CLOUD=1` and startup confirmation, following the
[official server setting](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features).
It exited cleanly; installed manifest hashes and existing key-file metadata
were unchanged. The shared daemon was not restarted or reconfigured. No model
was downloaded. This is a configured local-only run, not a network-isolation
attestation. Raw logs and owner-specific paths stay private.

## Reviewer handoff

Review the clipboard behavior in the actual target browser by pasting a synthetic
brief and comparing it to the displayed text and JSON. Inspect changed-pin late
responses separately from real clipboard transfer. In the semantic review, pay
particular attention to the conservative unknown-hardware decision: “not an
inventory” cannot establish that a model is absent.

Next accuracy work should address the four failed cases without hiding these
outputs, then freeze unseen defective and clean tasks for independent review and
paired final-host comparison. Do not tune against that held-out set. Accuracy,
broader host delivery, full accessibility, peak memory and whole-task cloud
savings remain unqualified or unknown. All shipped profiles remain unqualified.

The private acceptance record retains exact build hashes, source/installed test
logs, browser observations, screenshots and the checksummed trial packet. The
package version remains `0.4.0.dev8`; identify this UI correction by its interface
hash and Git revision. The pipeline identity covers Python code, not web assets.
