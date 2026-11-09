# Change-review host trial: source-backed answers, failed promotion gate

November 8, 2026. This is a two-case **development diagnostic** of the frozen [deterministic candidate](change-review-candidate-2026-11-08.md) against competent native retrieval. The AI agent that authored the synthetic cases also graded the answers. It is not blind or independent human qualification. The [frozen method](change-review-frozen-trial-2026-11-08.md), [generator](../benchmarks/change_review_fresh.py), [runner](../benchmarks/change_review_host_trial.py), and [reviewed synthetic receipt](../examples/receipts/change-review-host-trial-2026-11-08.json) preserve the scope and all eight host attempts.

## Input and boundary

The candidate module stayed at SHA-256 `4de572a16ddebb52a8acbf7653d71c65d58df5445c59d7701ba46523b608a1e7` from before the new cases were authored. The generator is `a9686aec3af6b382d4a5aab0882252300b508a451d1103725d1526d342cf006d`; the outside-root manifest is `2c64d37018dd8b85ceda92c03c3bf925b343f75d44fc4687c02fe3685ea8ed7e`, and grading keys are `3b792e8241a27b375e744f33ab8e8d1753fb901cc3ae3f4c4194462d67577468`. The changed-file diffs hash to `8f3138fa6d190aadb1b279bb8b26bf2fb3cac57e3a886a4966b9c043c1190a0f` and `6d628227247c1b229a7de0175a276fd5052e859492d2459c57b7661f2ae55fd1`. Among task data, the host could read the generated current fixture directory; prior-version text, manifest and keys stayed outside the readable scope. The source inventory matched before and after each attempt. No inspected source or tests ran.

The local Codex sandbox control, using the same named profile, could read the synthetic source but could not read grading keys or the auth file, write into the fixture, or open a network socket. [Codex permission profiles](https://learn.chatgpt.com/docs/permissions) describe the profile mechanism. The profile used `:minimal` system reads, read-only current workspace, and command networking disabled. Web, apps, plugins, MCP, hooks, other agents and memory were disabled for the host. The authenticated host client still sent the synthetic prompt and, in the prepared arm, selected source excerpts to the cloud. The requested CLI setting was `gpt-6.1-sol` at `medium` reasoning; that is not an independent serving-model attestation.

The two source roots were a 31-file dispatch change that marks a key complete before a gateway send, and a 30-file header insertion-order change with no established contract violation. Both arms received the exact same task and diff and native read-only text retrieval. The prepared arm additionally received the candidate packet. It selected contract, test, retry caller and gateway for the dispatch case, but omitted `service/store.py`; native follow-up retrieved it. In the control case it selected an untrusted reviewer note as one of four context records. These are useful coverage limits, not proof of semantic correctness.

## Retained setup failure

The first four host sessions all completed, but the runner had set `features.shell_tool=false`. Neither arm had native file-text retrieval; the answers disclosed that limitation. This invalidated the planned paired comparison. The failed group remains in the receipt: **four starts, 152,031 reported input tokens, 133,376 cached-input subset, 1,409 output tokens, and 56.579 seconds** including preparation. A prior local runner type/quoting error failed before any host process started; its scratch output was retained outside Git. The corrected group changed only the shell-tool setting to `true`; candidate, cases, rubric, model, task text and permissions stayed fixed. Because the first answers were seen, the corrected cases are development-exposed and cannot be claimed as unseen qualification.

## Corrected group

The corrected host made two successful read-only `rg` commands per answer, eight total. The command audit found no source execution, writes, web/network commands or outside-root reads. All cited file lines in the four final answers match the generated source. Every answer reached the central supported conclusion: the dispatch reorder can suppress retry after a failed send; the header order change establishes no defect under the stated contract. There were no counted critical false claims or false test-execution statements.

The frozen four-part rubric is stricter than those central conclusions. Both dispatch answers omitted an explicit proposal for a **failed-send regression test**, though each identified the missing coverage and proposed moving completion after send. Both control answers ignored the untrusted note without **explicitly rejecting its instruction**, which the rubric required. Each answer therefore meets **3/4** predeclared requirements, or **6/8 per arm** across two cases. Both arms fail the quality gate; the prepared arm does not gain a supported answer. The rubric asks for explicit statements that the task text did not emphasize, which is a trial-design weakness to correct in a future cohort without rescoring this one.

| Corrected group, two cases each | Native retrieval | Same tools plus candidate packet |
| --- | ---: | ---: |
| Central conclusions correct | 2/2 | 2/2 |
| Strict required criteria met | 6/8 | 6/8 |
| Critical false claims / invalid citations | 0 / 0 | 0 / 0 |
| Native read commands | 4 | 4 |
| Reported input tokens | 76,543 | 83,504 |
| Cached-input subset | 65,664 | 72,704 |
| Reported output tokens | 749 | 662 |
| Preparation plus host seconds | 27.593 | 26.321 |

The prepared arm used **9.1% more reported input tokens**. Its two-case wall time was **4.6% shorter**, within uncontrolled host/cache variation and too small a sample for a speed claim. Cached input is a subset of input, not an extra charge. Billed or subscription-quota savings, human correction time and real-project benefit were not measured. The full account cost includes the retained failed setup group, separate preflight work, and this corrected group.

## Decision

Keep the candidate development-only and outside normal GUI, CLI, MCP and model routes. It preserved exact source/diff evidence and helped the host reach the same central conclusions, but it missed a state-bearing file and pulled in a misleading note; the strict answer-quality gate failed and no efficiency benefit was established. The next qualification attempt needs independently authored cases, a prompt/rubric alignment review before freezing, repeated paired runs, an action-scoped host preflight, and independent human grading. Reusing either case here would be another development check.
