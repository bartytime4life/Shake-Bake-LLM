# The workbench copies the orientation brief by default

Recorded November 8, 2026 for `0.4.0.dev22`. **Copy brief**, the text
preview and **Save brief as .txt** now use the orientation layout by default.
The evidence layout stays one choice away under **Brief layout**. The JSON
record download is unchanged and still keeps every captured byte.

## Why

Two pre-registered host comparisons tested the orientation framing, frozen at
`e537327` in the CLI as `brief --style orientation`.

- **Six fresh cases:** the brief caused no losses
  ([record](orientation-comparison-2026-11-08.md)).
- **Eight multi-file fixes:** the hosts named more of the changed files with
  tools (11 against 9 of 19) and on the paste path (13 against 9).
  ([record](orientation-multifile-2026-11-08.md))
- **The evidence layout:** under the same method it lost four of twelve
  paired comparisons.

Pasting into a chat is the workbench's main use, and the paste path showed the
clearest gain.

## What the copied text contains

The default copy mirrors the frozen CLI renderer section for section. It has:

- the request;
- the starting-points guidance;
- one ranked file list with line ranges, context reasons and indexed line
  numbers, capped at fifteen files;
- near-duplicate warnings, at most four primary excerpts cut to twelve lines,
  and the scan limits.

The JavaScript constants and the near-duplicate rule match `briefing.py`.

The workbench adds four things the measured runs did not have:

1. **A line saying captured excerpts are not live access** or proof that
   tests ran. It is kept from the evidence layout's ground rules.
2. **An invitation to ask for a file or line range by path.** In a chat the
   user can paste what the assistant asks for.
3. **The local model's draft, when Local AI ran.** It sits under its own
   heading, labeled unverified, with a line saying it does not limit where to
   look. That line also says to ignore any instruction the draft repeats from
   the source, since the 8B worker is known to follow injected source
   instructions.
4. **The exact values section.** It holds the verbatim JSON request,
   evidence identities and hashes, so a copy can still be verified against
   the JSON record.

None of these four was measured. The first and fourth are safety and
verification text. The third only appears when the user turned Local AI on.

## Checks

- **Node clipboard suite:** 23 tests pass. The earlier tests pin the evidence
  layout byte for byte. Five new tests cover the following:
  - The default layout matches an independent rendering of the orientation
    text, and the copy keeps the exact request.
  - Context windows are listed with their reasons but not excerpted, long
    excerpts are cut at twelve lines, and near-duplicates are flagged.
  - Crafted paths and first lines stay in inline code, and the list stops at
    fifteen files.
  - A local model draft is labeled as a suggestion that cannot carry source
    instructions.
  - Switching layout re-renders the text and size, copy writes the chosen
    layout, and an unknown value falls back to the default.
- **Browser suites:** all eight pass in headless Chrome. The clipboard browser
  test checks the default, switches to the evidence layout, and confirms the
  choice is stored. A file launch still reads no storage, and the inert demo
  never writes the choice.
- **Python tests:** 238 tests pass.
- **Headless pass on this repository:** the picker sits below **Copy brief**,
  so keyboard focus still moves from the result title to Copy. There was no
  horizontal overflow at 1280 or 390 pixels and no console errors. The
  orientation copy was 6,990 bytes against 13,945 for the evidence layout on
  the same request.

## What this does not change or prove

- **The CLI default is unchanged.** `brief` still renders the evidence layout
  unless `--style orientation` is passed, and `assist` always uses the
  evidence layout.
- **It does not establish token savings or better answers in general.** The
  measured gain is limited to the two records above: Claude Code `sonnet`
  hosts on Long Code Arena issues.
- **The four workbench additions are untested with hosts.**
