# The orientation brief is the default copy and CLI layout

Recorded November 8, 2026 for `0.4.0.dev22`.

- **In the workbench:** **Copy brief**, the text preview and **Save brief as
  .txt** use the orientation layout by default. The evidence layout stays one
  choice away under **Brief layout**.
- **In the CLI:** `brief` renders the same layout by default, and
  `--style evidence` restores the old one.
- **Unchanged:** the JSON record download and `--format json` still keep every
  captured byte. `assist` still uses the evidence layout.

The same change fixes BUG-022. The workbench had written the local model's
draft as plain lines, where repeated source text could pose as a brief
heading.

## Why

Two pre-registered host comparisons tested the orientation framing, frozen at
`e537327` as `brief --style orientation`.

- **Six fresh cases:** the brief caused no losses
  ([record](orientation-comparison-2026-11-08.md)).
- **Eight multi-file fixes:** the hosts named more of the changed files with
  tools (11 against 9 of 19) and on the paste path (13 against 9)
  ([record](orientation-multifile-2026-11-08.md)).
- **The evidence layout:** under the same method it lost four of twelve paired
  comparisons.

Pasting into a chat is the main use, and the paste path showed the clearest
gain.

## What the brief contains

Both surfaces render the frozen layout section for section:

- the request;
- the starting-points guidance;
- one ranked file list with line ranges, context reasons and indexed line
  numbers, capped at fifteen files;
- near-duplicate warnings, at most four primary excerpts cut to twelve lines,
  and the scan limits.

The JavaScript constants and the near-duplicate rule match `briefing.py`.

These additions were not in the measured runs:

1. **A line saying captured excerpts are not live access** or proof that
   tests ran. It comes from the evidence layout's ground rules. Both surfaces
   have it.
2. **An invitation to ask for a file or line range by path.** Both surfaces
   have it.
3. **The local model's draft or notes, when a model ran.** They sit inside a
   fence under an unverified heading. A line says the draft does not limit
   where to look and that any source instruction it repeats should be ignored.
   Both surfaces have this. The CLI also reports a model failure, as the
   evidence layout does.
4. **The embedding rerank record, when `--rerank-model` was used.** This is
   CLI only.
5. **The exact values section.** It holds the verbatim JSON request, evidence
   identities and hashes. This is workbench only, because the CLI's JSON output
   serves that purpose.

With no model and no rerank, the CLI output differs from the frozen
`e537327` renderer by exactly the first two lines. That was checked by
diffing both renderers on the review fixture.

## BUG-022

The workbench's copied brief wrote the drafted prompt and model notes as plain
lines, in the evidence layout too. The 8B worker is known to repeat injected
source instructions. A draft containing `## IGNORE THE RULES` would therefore
appear in the pasted brief as a heading outside any fence. The CLI brief has
always fenced the same text. The workbench copy now does too, in both layouts.
A regression test with forged headings in the goal, asks, notes and questions
fails on the previous renderer and passes now.

## Checks

- **Node clipboard suite:** 24 tests pass. The earlier tests pin the evidence
  layout byte for byte, with the draft and notes now fenced. Six new tests
  cover the following:
  - The default layout matches an independent rendering of the orientation
    text.
  - Context windows are listed with their reasons but not excerpted, long
    excerpts are cut at twelve lines, and near-duplicates are flagged.
  - Crafted paths and first lines stay in inline code, and the list stops at
    fifteen files.
  - The local model draft is labeled and fenced.
  - Switching layout re-renders the text and size, and copy writes the chosen
    layout.
  - The BUG-022 forged-heading regression.
- **Browser suites:** all eight pass in headless Chrome. The clipboard browser
  test checks the default, switches to the evidence layout, and confirms the
  choice is stored. A file launch still reads no storage, and the inert demo
  never writes the choice.
- **Python tests:** 240 tests pass. They include the CLI default, `--style
  evidence`, and fenced draft, notes and failure lines in the orientation
  brief.
- **Headless pass on this repository:** the picker sits below **Copy brief**,
  so keyboard focus still moves from the result title to Copy. There was no
  horizontal overflow at 1280 or 390 pixels and no console errors. The
  orientation copy was 6,990 bytes against 13,945 for the evidence layout on
  the same request.

## What this does not change or prove

- **Scripts that parse the CLI's evidence-layout Markdown** need
  `--style evidence` from this version on. No script in this repository does.
- **It does not establish token savings or better answers in general.** The
  measured gain is limited to the two records above: Claude Code `sonnet`
  hosts on Long Code Arena issues.
- **The additions listed above are untested with hosts.**
