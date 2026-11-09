# Where host context tokens go at the start of a task

Status: analysis of retained records plus two local measurements, November 6,
2026. No new cloud runs. The question is what makes Claude and GPT spend tokens
before they can answer, so that preparation targets those processes instead of
shrinking text that is already small. Counters come from the
[native-retrieval comparison](native-preparation-2026-11-05.md) (sixteen Codex
attempts with shell tools) and the [host-note diagnostic](host-note-diagnostic-2026-11-05.md)
(twenty single-turn Codex attempts with tools disabled). Both are synthetic
development material. Nothing here is a billing or quota claim.

## Findings, ranked by how much they explain

### 1. Turn count multiplies everything

Each tool call is a new model turn. The host resends the fixed harness context
(system prompt, tool definitions, project instructions), the request and every
earlier tool result, then adds the new result. Reported input therefore grows
with the number of commands, not with how much those commands returned.

| Attempt | Commands | Command output | Reported input | Cached subset | Output |
| --- | ---: | ---: | ---: | ---: | ---: |
| dispatch-path, native, repeat 1 | 11 | 5.5 KB | 53,210 | 49,792 | 2,054 |
| dispatch-path, native, repeat 2 | 11 | 6.0 KB | 52,394 | 48,640 | 2,150 |
| publish-reorder, native, repeat 1 | 13 | 7.4 KB | 68,101 | 52,736 | 2,313 |

Eleven commands that returned about 1,400 tokens of text cost 53,000 reported
input tokens, 94% of it cache reads. Across the sixteen attempts the average
reported input per command turn was 4,200 to 11,500 tokens. Prompt caching makes
the resent prefix cheaper, not free, and every turn adds latency.

The single-turn runs put a floor under this. With tools disabled and a brief of
roughly 500 to 700 tokens, each answer cost 12,000 to 12,500 input tokens, and
the 11,008-token cached prefix that appeared when a case's second arm ran soon
after its first is the stable part of that context. The retained counters do
not say how the host apportions the fixed prefix across turns, so the two
figures are reported separately rather than reconciled.

### 2. Broad reads are the second driver, and they partly waste themselves

| Attempt | Commands | Command output | Reported input | Input minus cached | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| two-log-failures, native, repeat 1 | 6 | 97.8 KB | 74,649 | 25,497 | 63.9 |
| two-log-failures, native, repeat 2 | 10 | 97.9 KB | 86,647 | 25,719 | 61.1 |
| deployment-unknowns, native, repeat 1 | 8 | 591.2 KB | 92,673 | 27,393 | 128.2 |
| deployment-unknowns, native, repeat 2 | 9 | 296.2 KB | 114,656 | 19,552 | 61.5 |
| same four cases, prepared arm | 5–11 | 5.7–15.9 KB | 42,299–62,520 | 15,278–18,488 | 51.3–83.3 |

Reading a whole log or dumping a directory returns far more text than the host
can use. 591 KB is more than the attempt's entire reported input, so the client
truncated it before the model saw it; the host paid for a cut-off head and then
searched again. These four attempts account for most of the 24.35% input
reduction in the comparison. On the two cases without a large read, the prepared
arm cost the same or more (dispatch-path: 53,210 native against 58,753 and
80,145 prepared).

### 3. The brief itself is cheap; its gaps are what cost

Local measurements of the shipped output, evidence only:

| Output | Size | About |
| --- | ---: | ---: |
| CLI brief, repo-tour case, markdown | 1,904 B | 476 tokens |
| CLI brief, coverage-budget case, markdown | 1,644 B | 411 tokens |
| Workbench handoff text, starter demo | 2,670 B | 667 tokens |
| of which exact excerpts | 389 B | 97 tokens |
| of which pretty-printed JSON framing | about 2,000 B | about 500 tokens |

Compacting the JSON would save roughly 100 tokens per brief. That is noise next
to one avoided command turn. The real cost in the prepared arm was that the
brief omitted controlling context (dispatch settings and routing, the
change-review contracts and test), so the host still ran 75 commands against the
native arm's 79. The prepared arm's higher uncached input (15,000 to 20,000
against 3,400 for dispatch-path native) is the brief and the host's own
re-discovery being read fresh.

### 4. Things that do not matter much

- The app's MCP server exposes five tools with about 740 bytes of descriptions,
  a few hundred tokens of a host's base context.
- Output tokens were 1,800 to 2,700 per attempt in both arms. Answer length is
  not where the budget goes.
- Local preparation time was 0.08 seconds per attempt.

### 5. Claude Code was not measured here

Claude Code resends the same kind of base context every turn: its system prompt,
built-in tool schemas, `CLAUDE.md` or `AGENTS.md`, memory files and the tool
definitions of every connected MCP server. That base can be several times
Codex's because MCP definitions are loaded up front. A measurement with
`claude -p` in this session failed because the CLI was not signed in. On the dev
PC, one trivial prompt with `--output-format json` in an empty directory and
again inside the repository gives `cache_creation_input_tokens` for both; the
difference is what the repository's instruction files add.

## What to target

1. **Fewer host turns before the first supported answer.** This is the only
   lever that scales. The brief must carry the controlling context the host
   otherwise goes looking for: the configuration that governs the behavior in
   question, the callers or contracts of the changed code, the relevant test,
   and a small map of the files it may want next. Measure commands per attempt
   and the share of attempts answered with zero commands. Seventy-nine to
   seventy-five was not a result.
2. **Replace broad reads with ranged excerpts and counts.** For logs and large
   files, hand over the matching lines with their line numbers and the match
   counts the host would otherwise grep for. For orientation, a path list with
   sizes and one-line roles beats letting the host list and open files.
3. **Keep the brief prefix-stable.** Put fixed instructions and exact evidence
   first and volatile fields (job IDs, timestamps, usage, routing) last, so a
   follow-up turn in the same host session reuses the cached prefix. The
   present handoff text already ends with the receipt; the job ID line near the
   top is the one early field that changes per brief.
4. **Do not spend effort shrinking the brief.** It is 400 to 700 tokens.
5. **Advise a lean host for Shake & Bake sessions.** Base context belongs to the
   host, not the app. A Codex or Claude Code profile with no unrelated MCP
   servers, or the paste-into-chat path with no tool schemas at all, makes a
   complete brief cheapest. This is user guidance, not something the app can
   enforce.

Where the local model fits this: not as a summarizer, which the host-note
diagnostic already showed adds nothing, but as the selector that decides what
controlling context belongs in the brief before the host starts. The current
`handoff_prompt_v1` design points the host at evidence; it does not yet widen
what is collected.

## What to measure next

- Retain command text, not only counts, in the comparison runner, so each
  command can be classed (listing, whole-file read, search, ranged read, log
  read) and the class totals compared across arms.
- Record per-attempt commands before the first cited answer and whether a
  follow-up turn was needed after the brief.
- Measure Claude Code base context on the dev PC as described above, with and
  without the user's MCP servers.
- Any retrieval change is a new candidate on new frozen cases; the four
  comparison projects are exposed.

## What this does not establish

- Billing or subscription-quota savings. Cached and uncached input are priced
  differently and the counters here are host-reported.
- Behavior on real private repositories or with Claude Code, which was not run.
- How the host apportions its fixed prefix across turns; the 12,000-token
  single-turn figure and the 4,400-token per-turn average are both retained.
- That a more complete brief would reduce turns; that is the hypothesis for the
  next frozen comparison, not a result.
