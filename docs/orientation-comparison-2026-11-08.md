# Orientation brief on six fresh cases: no harm, no clear gain

Status: completed November 8, 2026, under a protocol pushed as `908d627`
before any fresh row was read. The candidate is the orientation brief frozen
at `e537327` (`0.4.0.dev21`, `brief --style orientation`), designed after the
[host comparison](host-comparison-2026-11-08.md) and
[paste-path comparison](paste-comparison-2026-11-08.md) showed the evidence
brief anchoring hosts on its excerpts. The tools-path rule is met on a margin
of one file; the paste-path rule is not. The useful finding is the absence of
the harm the evidence brief caused.

## What the candidate changes

Same collected evidence, different framing: it says the places found are
starting points and the fix may involve unlisted files; one ranked list of
files with line numbers replaces separate excerpt, context, map and index
sections; near-duplicate code in different files is flagged; at most four
primary excerpts are shown, cut to twelve lines; the "Answer with" section is
gone. On these cases it was 3.6 to 8.5 KB, against 8.7 to 14.1 KB for the
evidence brief on the earlier cases.

## Fresh cases

Six never-read Long Code Arena `dev` rows from offsets 300 to 699: microsoft
recommenders, faker, textual, pre-commit, rasa and manim. The pool excluded
every reserved `test` id (28 of them lie in those offsets; they were excluded
by id and not displayed) and every repository used in the earlier external or
frozen runs. One case per repository, chosen by hash, no omissions, 94 MB
fetched. The selection record is committed; no issue text is.

## Results

Files named out of 11 that the fixing pull requests changed:

| Arm | Hits | Median tool calls | Median tokens | Median seconds |
| --- | ---: | ---: | ---: | ---: |
| Tools, no brief | 6 | 4 | 86,984 | 11.0 |
| Tools + orientation brief | **7** | 3.5 | 88,081 | 11.6 |
| No tools, issue only | 6 | 1 | 82,047 | 6.7 |
| No tools, issue + orientation brief | 6 | 2 | 84,938 | 7.8 |

- **Tools path:** one win (faker, where the host also named the test file),
  no losses. Hits 7 against 6 and median tool calls 3.5 against 4, so the
  registered rule is met, even though reading the brief costs that arm one
  tool call. Median tokens were still higher, by about 1,100.
- **Paste path:** a tie on every case, 6 against 6; the rule is not met.
- **Where it missed:** in microsoft recommenders the changed file
  (`scripts/generate_conda_file.py`) was not in the orientation brief at all,
  so both paste arms guessed the wrong directory. That is a collector recall
  miss, not a framing effect.

## Reading it against the earlier runs

| Comparison | Brief hits | No-brief hits | Brief losses |
| --- | ---: | ---: | ---: |
| Evidence brief, tools (earlier six cases) | 7 | 14 | 3 |
| Evidence brief, paste (earlier six cases) | 9 | 10 | 1 |
| Orientation brief, tools (fresh six) | 7 | 6 | 0 |
| Orientation brief, paste (fresh six) | 6 | 6 | 0 |

The evidence brief lost files in four of twelve paired comparisons; the
orientation brief lost none in twelve. That supports the anchoring diagnosis
and says the reframing removes the harm. It does not show a benefit: the fresh
cases are easier (four of six have a single gold file, which every arm found),
so the sample cannot separate a small gain from noise, and tokens were higher
with either brief.

## What this establishes and what follows

- On this sample, the orientation framing does not narrow the host's answer
  the way the evidence framing did, and it is about half the size.
- It does not establish token or tool-call savings, better answers in
  general, or anything about ChatGPT, other Claude models or harder
  multi-file issues.
- The evidence layout is the one the workbench copies today. Given four losses
  against none, the orientation framing is the safer layout to ship, but
  porting it to the workbench is a product decision, and a larger fresh sample
  weighted toward multi-file fixes is what would show whether it helps rather
  than merely does no harm.

Run data (usage, named files, hits, input hashes; no issue text) is under
`benchmarks/orientation-comparison-2026-11-08/`.

Follow-up: the larger multi-file sample ran the same day and met both gain
rules; see [the multi-file record](orientation-multifile-2026-11-08.md).
