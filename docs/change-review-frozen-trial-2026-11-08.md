# Change-review paired trial: frozen setup

Frozen November 8, 2026, before authoring the new synthetic cases or seeing host answers. This is a development comparison, not independent qualification.

The development-only candidate is `src/shake_bake/change_review.py`, SHA-256 `4de572a16ddebb52a8acbf7653d71c65d58df5445c59d7701ba46523b608a1e7`. Its focused tests are SHA-256 `3e24005683d587a4fd3f1d360451c2d13094a564cd3138a16170a0b6bcb3b3db`; the exposed packet check is SHA-256 `68050824db9006e57506929e7e62f5f1211ebcc426a790b51b77eb3fd28fc816`. No candidate adjustment is allowed after inspecting the new cases or outcomes under this trial identity.

## Method and gates

- Create two new inert synthetic change reviews after this freeze: one change with a cross-file failure consequence and one without a confirmed defect. Keep prior-version text, grading criteria, and manifest outside each inspected source root. Record source and diff hashes before host runs.
- Both arms receive the same exact original task and diff, the same current source root, the same read-only native retrieval tools, host model/settings, deadline, and instruction not to execute source or tests. The prepared arm additionally receives the unchanged candidate's rendered exact-source packet. Separate fresh sessions; alternate arm order across cases. No local model.
- Pin the signed-in Codex CLI to `gpt-6.1-sol` with `medium` reasoning, a 180-second per-attempt deadline and no orchestrator retry. Run checkpoint native, checkpoint prepared, control prepared, control native. Turn off web, apps, plugins, MCP, hooks, other agents and memory in the CLI configuration. Audit actual tool actions afterward. The host model identifier is a requested setting, not independent serving-model attestation.
- Assess the final answer for each case against case-specific required findings, support by cited exact source, correct uncertainty, and critical false claims. Record missing/invalid answers, every host attempt, commands, preparation and host time, input/cached/output usage where reported, and source integrity. Do not silently retry or tune the candidate.
- The quality gate requires both prepared answers to meet every required finding, no critical false claim or false execution statement, and no supported baseline case lost. An incomplete or failed attempt counts as a failure. A minimum of two cases and one run per arm is diagnostic only: it cannot establish repeatable speed, billing savings, real-project benefit or product promotion. Any efficiency result is descriptive, never a promotion decision here.

The existing exposed `publish-reorder` derivative is excluded. This root AI agent authors and grades the new cases, so the assessment is not blinded or independent human review.
