# Host comparison on six real issues: the brief did not help

Status: completed November 8, 2026, under a protocol pushed as `47cad34`
before any run. This is the first measurement in this project of the question
it exists for: does pasting the brief make a cloud host do less work for the
same or better answer? On this sample the answer is no. The pre-registered
rule is not met, and the brief arm named half as many of the files that
actually changed.

## Setup

- **Host.** Claude Code subagents of one type (general-purpose) on one model
  (the `sonnet` alias), one run per case and arm, all started together. The
  host-reported figures are tool calls, tokens (including cached input) and
  wall time.
- **Cases.** The first six of the twelve frozen-run Long Code Arena cases
  (pysyft, openbbterminal, sanic, netbox, pip, dvc), now exposed. Each
  repository was copied without `.git` and without a remote. The issue text
  had no URL or number. The gold, the changed files of the fixing pull
  request, was kept outside the case directories.
- **Task.** Name up to five files that must change, on a final `FILES:` line.
  Read only inside the case directory, no web, no git, no edits.
- **Arms.** Native: issue and repository. Brief: the same plus `brief.md`, the
  evidence-only CLI brief from the frozen `dev20` collector (8.7 to 14.1 KB),
  which the host was told to read first. That read costs the brief arm one
  tool call, a bias against it that was left in.
- **Third arm not run.** The brief with the local model's drafted prompt was
  planned, but the `qwen3.5:4b` worker refused five of six cases with
  `worker_context_budget`: a real issue plus its excerpts exceeds the
  worker's 6,000-byte source cap. On those cases the arm would equal the
  brief arm.

## Results

| Arm | Median tool calls | Mean tool calls | Median tokens | Median seconds | Files hit / 25 gold | Files named |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Native | 4 | 4.33 | 86,103 | 13.4 | **14** | 18 |
| Brief | 3 | 4.33 | 88,523 | 10.8 | **7** | 18 |

| Case | Gold files | Native: calls / tokens / hits | Brief: calls / tokens / hits |
| --- | ---: | --- | --- |
| pysyft | 4 | 8 / 89,242 / 2 | 11 / 95,634 / 1 |
| openbbterminal | 2 | 3 / 83,714 / 1 | 2 / 86,841 / 1 |
| sanic | 3 | 2 / 84,322 / 3 | 3 / 87,795 / 3 |
| netbox | 9 | 4 / 87,766 / 4 | 3 / 88,337 / 1 |
| pip | 3 | 4 / 90,214 / 0 | 4 / 92,287 / 0 |
| dvc | 4 | 5 / 84,439 / 4 | 3 / 88,709 / 1 |

**Registered decision: not met.** Median tool calls were lower with the brief
(3 against 4) but the mean was identical, median tokens were higher (88,523
against 86,103), and hits fell from 14 to 7.

## What the numbers say

1. **Tokens rose in every case.** The brief added 600 to 6,400 tokens per run
   and saved none. The host's fixed context, about 80,000 tokens of system
   prompt and tool definitions per run here, dwarfs both the brief and the
   work. This is the turn-count effect from the
   [host context cost analysis](host-context-cost-2026-11-06.md) seen from
   the other side: on tasks the native host solves in two to eight calls,
   there are few turns left for a brief to remove.
2. **The brief narrowed the answer.** In netbox and dvc the native host
   followed the pattern across the codebase and named four of the changed
   files; with the brief it named the one or two files the brief excerpted
   and stopped. Openbbterminal shows the same anchoring the other way: the
   brief's second excerpt was a look-alike copy of the function in another
   module, and the host named it instead of the real second file.
3. **Neither arm is better on wall time in total.** The brief arm was faster
   in the median but slower in total (108 s against 85 s), driven by one long
   pysyft run.

Possible reasons, all hypotheses that this sample cannot separate: the brief's
excerpts read as the answer's boundaries rather than a starting point; its
"Answer with" section asks for findings rather than a complete change list;
the "read it first" instruction front-loads a frame; or localization of a
multi-file change is simply a task where exploration beats preselection.

## What this does and does not establish

- On six real Python issues, one host model and one run each, the
  evidence-only brief did not reduce host cost and reduced how many changed
  files the host named. That is evidence against the core claim in its
  current form, not proof of the opposite in general.
- It does not cover ChatGPT, other Claude models, the paste-into-chat path
  without tools (where the brief is the only source and may matter far more),
  answer correctness beyond file names, or repeat-to-repeat variance.
- Public issues may be in the host's training data, equally in both arms. The
  host's own tool calls were not audited; isolation was by instruction.

## What follows

Given this result, more collector tuning is not the next step. The most
likely remaining place for the brief to help was the no-tools paste path; the
[paste-path comparison](paste-comparison-2026-11-08.md) run straight after
found no benefit there either (9 against 10 of 25 files, no case won). The brief's framing (excerpts presented as a starting
point, an explicit request to look beyond them, no "answer with" section that
narrows the scope) is a second candidate, to be frozen before it is measured.

Run data (usage, named files, hits; no issue text) is under
`benchmarks/host-comparison-2026-11-08/`.
