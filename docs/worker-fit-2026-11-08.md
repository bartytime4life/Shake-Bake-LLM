# The local model gets a fitted copy instead of refusing real tasks

Recorded November 8, 2026 for `0.4.0.dev23`. This fixes BUG-023.

## The defect

The worker sends the local model one JSON message holding three things:

- the original request;
- scan facts;
- every captured excerpt.

It refused the whole job with `worker_context_budget` when that message
passed 6,000 bytes. Since `0.4.0.dev10`, the controlling-context pass and a
16 KB excerpt budget allow up to ten records, and a real issue's text can be
several kilobytes. So with Local AI on, most real repositories got no draft:

- **The November 8 host comparison:** five of six issues were refused
  ([record](host-comparison-2026-11-08.md)).
- **The eight multi-file issues measured today:** seven were refused.

The synthetic demo and the Task Lab fixtures fit under the cap, so no suite
noticed.

## The change

When the full message fits, nothing changes. The bytes sent are identical to
before, and a test compares them with the earlier construction.

When it does not fit, the model gets a fitted copy:

1. Every excerpt is cut to twelve lines, the same cut the orientation brief
   uses. Each cut record carries `text_cut` and `shown_end_line`.
2. Records are left out from the end until the message fits. Context windows
   come after the primary excerpts, so they go first. A `worker_view` note
   lists what was left out.
3. If not even one record fits beside the unchanged request, the job is
   still refused.

The constrained-decoding schema lists only the records the model was shown,
so it cannot cite one it never saw. The note records the view. Every brief
then states it, in the CLI's two layouts, in both workbench layouts and in
the workbench's draft caption:

> The local model saw a shortened copy: it was shown E1, E2 (E2 cut to 12
> lines) and was not shown E3, E4. Every excerpt in this brief is unchanged.

The exact excerpts in the brief and the JSON record are not touched. The 6,000
byte cap, the instructions and the requested model settings are unchanged.

## Development check on exposed cases

These are the eight multi-file Long Code Arena issues from the
[multi-file run](orientation-multifile-2026-11-08.md), with `qwen3.5:4b` on
this PC. It was run once before and once after the change. The cases are
already exposed, and nothing here measures draft quality.

| Code | Draft produced | Refused |
| --- | ---: | ---: |
| Before | 1 of 8 | 7 (`worker_context_budget`) |
| After | 8 of 8 | 0 |

- **Records shown:** after the change the model saw 1 to 7 of each case's 6
  to 10 records, and the one case that already fit was unchanged.
- **Nothing was cut:** no excerpt needed cutting, because the collector's
  windows are already shorter than twelve lines. All fitting came from leaving
  out trailing records.
- **Long requests take the room:** in the conan case the issue text left space
  for only one record.
- **Time:** each draft took 4.6 to 7.2 seconds.

## What this does not establish

- **No measure of draft quality or help.** Whether the draft helps a host, or
  re-narrows its search the way the evidence brief's answer section did, is
  unmeasured.
- **No new accuracy claims.** The 8B worker's known weakness with injected
  source instructions is unchanged. The draft stays fenced and labeled
  unverified.
- **No model is qualified,** and no profile changes.
