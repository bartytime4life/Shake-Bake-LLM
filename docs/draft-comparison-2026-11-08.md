# The local model's draft on six fresh cases: no effect shown

Status: completed November 8, 2026. The protocol was pushed as `ceec69a`
before any row at `dev` offsets 1200 to 1699 was read
(`benchmarks/draft-comparison-2026-11-08/protocol.json`).

The question was whether adding the local model's drafted prompt to the
orientation brief helps a Claude host. Neither registered rule was met, and
no harm was shown either. Under the protocol, Local AI stays optional, and the
brief makes no claim for the draft.

## What was compared

- **Candidate:** commit `a49268a` (`0.4.0.dev23`), whose fitted worker copy
  first made drafts possible on real issues. The source hashes were checked
  before rendering.
- **Control brief:** the default orientation brief.
- **Draft brief:** the same command with `--model qwen3.5:4b` on this PC's
  loopback Ollama. The model digest was the same before and after rendering.
- **Arms:** both briefs were given to the host with repository tools and on
  the no-tools paste path. That makes four arms, with prompts identical to the
  earlier orientation runs.
- **Host:** Claude Code `general-purpose` subagents on the `sonnet` alias, one
  run per case and arm.

## Cases

Eight never-read Long Code Arena `dev` rows were selected by the registered
hash rule from 500 rows: 239 were excluded as not multi-file and 107 for
size. Two selected checkouts exceeded the registered 300 MiB cap: fiftyone at
649 MB and deepchem at 453 MB. They were omitted without replacement, as the
protocol requires.

That leaves six cases with 13 changed files: brownie,
pytorch-metric-learning, codechecker, graphite-web, autobahn-python and ptvs.
The worker drafted on all six. Five used a fitted copy that left out two to
six trailing records, and none were cut. No issue text is committed.

## Results

Changed files named in the top five, out of 13:

| Arm | Hits | Median tool calls | Median tokens | Median seconds |
| --- | ---: | ---: | ---: | ---: |
| Tools + orientation brief | 8 | 4 | 87,608 | 10.9 |
| Tools + orientation brief with draft | 8 | 4 | 88,239 | 12.8 |
| Paste, orientation brief | 9 | 2 | 83,812 | 9.9 |
| Paste, orientation brief with draft | 9 | 2 | 84,863 | 7.6 |

- **Tools path:** 8 against 8, with one win and one loss.
  - **Win:** pytorch-metric-learning, where the draft host also named the
    test file.
  - **Loss:** autobahn. The draft pointed the host at unrelated excerpts: a
    Twisted file, a protocol constant and a types module. The host then named
    the websocket and rawsocket modules instead of the changed `component.py`.
- **Paste path:** 9 against 9, with one win and one loss.
  - **Win:** brownie, where the draft host added `datatypes.py`.
  - **Loss:** graphite-web, where the control host's fifth file was the
    changed test file.
- **Isolation:** all 24 transcripts were audited, with no violations.

## What the drafts contained

- **Coverage:** the control brief listed 9 of the 13 changed files, and the
  draft sections named 5 of them.
- **No new files:** the draft never named a changed file that the control
  brief lacked.
- **Read-first lists:** the drafts were careful to cite only records they had
  been shown. Their read-first lists still included unrelated excerpts, such
  as the protocol constant in autobahn.
- **How hosts treated them:** one paste host said it ignored the draft because
  the draft only remarked that the excerpts did not show the call sites.

## What this establishes and what does not

- **No effect shown:** on six cases, with one local model at one setting, the
  draft neither helped nor hurt a Claude host's file list. It added about
  600 to 1,000 tokens at the median.
- **No harm shown:** this is not the anchoring harm the evidence brief caused.
  The orientation framing and the disclaimer appear to keep the draft from
  narrowing the host.
- **Not covered:** other models, larger samples, other task kinds and
  ChatGPT. Six cases cannot separate a small effect from noise.
- **For the product:** Local AI is worth keeping for its other uses, such as
  the visible draft and the notes. There is no measured reason to promote it
  as making assistant answers better.

Run data is in `benchmarks/draft-comparison-2026-11-08/`, in the files
`result.json`, `selection-record.json` and `acquisition.json`. It holds usage,
named files, hits, brief and issue hashes, the fitted-copy views and the
isolation audit, but no issue text.
