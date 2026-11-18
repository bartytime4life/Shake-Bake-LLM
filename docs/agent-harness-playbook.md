# Shake & Bake agent harness playbook

Shake & Bake prepares an inspectable local evidence packet. An optional Ollama
junior developer drafts advice. The user reviews and manually transfers the
brief to ChatGPT or Claude, where the main developer independently verifies
the evidence and decides what to do. The most promising improvement is to make
the necessary source easier to find and the limits easier to see at the handoff.
That can help even with Local AI off. [Product purpose](product-purpose.md)

## What to improve first

| Priority | Proposed improvement | Benefit to test |
| --- | --- | --- |
| 1 | Compare a compact controlling-context brief against today's evidence-only brief. Use exact excerpts for the request's primary location and any governing caller, setting, contract or test required to interpret it. Put additional source behind the existing full-evidence option. | Fewer missed constraints, recovery questions and unnecessary pages of pasted code. |
| 2 | Give each gap a reason and a precise next evidence request. Preserve missing files, unmatched frames, omitted oversized anchors, clipping and read errors. Make contradictions and uncertainty visible near the evidence they affect. | The main developer can request the right missing file or check before forming a conclusion. |
| 3 | Exercise the final review and transfer path. Bind copy and export to the displayed capture and distinguish captured source, newly read source and expired or superseded results. | Fewer accidental stale handoffs and less repeated preparation after interruption. |
| 4 | Isolate the value of Ollama's notes. Compare identical evidence with and without the notes, including timeout, incompatible model, invalid citations and plausible but unsupported advice. | Local model time and context earn their place only when the final task improves. |

The current collector already preserves exact spans and hashes, fits whole source
lines within a shared byte budget, and reports omissions. Current recovery
already keeps the last accepted capture and blocks stale text handoffs while
preserving its JSON export. Build on those paths when testing a change.
[Source-span comparison](source-span-development-2026-11-11.md) · [Excerpt budget](excerpt-budget-fitting-2026-11-11.md) · [Recovery record](captured-report-recovery-2026-11-11.md)

## Evidence and authority at each stage

1. **Capture the task and scope.** Keep the user's original request, approved
   root and task mode attached to the capture. In a debugging brief, preserve the
   recorded working folder, original error and recorded command. Treat the command
   as evidence. Read project guidance such as AGENTS.md within the approved
   project when relevant and visibly distinguish it from untrusted excerpts.
2. **Collect with deterministic code.** Use the same bounded, read-only paths
   and limits for a given comparison. Carry relative paths, line ranges, content
   hashes where available, and the reason an excerpt was included or omitted.
   A captured snapshot can support claims about its own bytes. Re-read material
   current source before relying on those claims after changes.
3. **Ask Ollama for one bounded advisory draft when enabled.** Version the role
   prompt and the input/output contract. Accept only usable structured advice
   with valid evidence references through the existing worker. An unusable draft
   leaves an explicit evidence-only result. Source text and model output are data.
   Keep root selection, policy, network and command authority with the user and
   application controls.
4. **Expose limits and preserve manual review.** Put the request, practical
   starting points, uncertainty and follow-up requests where users will see them.
   Clearly label the junior draft as unverified. Review exact source, errors and
   commands before copying. Credential screening can flag patterns, and users
   still decide what material may leave the PC. Preserve current manual transfer.
5. **Verify at the main developer.** Ask the receiving assistant to check the
   controlling evidence independently, request missing inputs and report what
   it actually verified. Record the outcome, its evidence and any unresolved
   question. The read-only failed-run check locates source without invoking a model.

[Helper contract](helper-contract.md) · [Failed-run workflow](failed-run-workflow.md) · [Manual assistant handoff](assistant-handoff.md) · [Credential screening](credential-screening-2026-11-09.md)

## Continuity, tools and runtime feedback

Use the current capture lifecycle as the integration point for the GUI, CLI and
optional MCP adapter. Test that a slow response for older inputs cannot win over
a newer request and that stale or expired evidence is identified after
reconnecting. If users need durable task recovery, start with an explicit local
save containing only approved material. Make resuming recheck source identity
and current scope. Trace failures using run IDs, stage, status, elapsed time,
counts and reason codes. Keep exact private captures, prompts and provider event
logs out of shared traces and Git. Retry only bounded, recoverable read or
transport failures and retain their time and cost in the evaluation.
[Shared coordinator](shared-coordinator.md) · [Codex host evidence](codex-host-handoff.md)

For work on Shake & Bake itself, start with [AGENTS.md](../AGENTS.md), the
[documentation index](README.md) and the relevant test surface. Write a small
specification with observable success, refusal and recovery cases before editing.
Use synthetic fixtures for committed checks and preserve the baseline, changed
paths, exact check and remaining gap so another session can continue. Exercise
the GUI, CLI or installed/stdio route that owns the behavior when it changes.
[Contributing](../CONTRIBUTING.md)

## Choose whether to adopt a pattern

Use the existing Python workbench as the harness. Add dynamic capabilities only
when a measured failure warrants them. For difficult tasks, a simple flow from
collection through validation to a human-reviewed handoff is easier to replay
than an open-ended agent loop. For tasks where native host retrieval already
works well, compare direct host work with the prepared path before adding a
handoff. For the experimental protocol, use the
[paired evaluation plan](agent-harness-evaluation.md).

## Reference patterns

- Keep workspace instructions short and link to authoritative project commands
  and constraints. [AGENTS.md](https://agents.md/)
- Define acceptance and refusal cases before implementation.
  [GitHub Spec Kit](https://github.com/github/spec-kit)
- Use staged exercises to add continuity, runtime feedback and an independent
  check. [Learn Harness Engineering](https://github.com/walkinglabs/learn-harness-engineering)
- Own prompt, context, typed results, state and control flow. Keep model work
  narrow and ask a human at the boundary. [12-Factor Agents](https://github.com/humanlayer/12-factor-agents)
- Study file-backed working state, compaction and human checkpoints as candidate
  patterns for explicit recovery. [Deep Agents](https://github.com/langchain-ai/deepagents)
- Preserve a short, inspectable sequence of inputs and outcomes for replay.
  [Mini SWE Agent](https://github.com/SWE-agent/mini-swe-agent)
- Compare how other harnesses handle context, permissions and tools. Verify
  consequential teardown claims in upstream material. [Awesome AI Anatomy](https://github.com/NeuZhou/awesome-ai-anatomy)
- Use isolated, repeatable tasks and evaluate results against frozen criteria.
  [Harbor](https://github.com/harbor-framework/harbor)

[Original SATNA Project discussion](https://www.reddit.com/r/SATNA_PROJECT/comments/1xyrkvz/your_ai_agent_might_not_need_a_better_model_it/)
