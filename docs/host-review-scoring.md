# Receipt-bound public host review

`benchmarks/public_host_review.py` closes a reporting gap in the public
change-review runner. It binds a separate review to the exact selected receipt
and retained answer bytes, validates judgments, and reports both trial progress
and review progress. It runs entirely offline: it does not call a host or model,
read fixture source or reference findings, judge correctness, or change routing.

Use the **private raw** `receipt.json` produced by
`benchmarks/change_review_public_trial.py`. The sanitized public aggregate in
`examples/receipts/` is a different document and is refused. Keep the receipt in
its original run folder, with the derived `NN-case-arm/answer.md` files intact.
These files and review sheets can contain source excerpts or private answers;
keep them outside the checkout.

The runner already creates `review-packet.json` after a complete trial. Review
each entry against pinned source and references, retain its answer text and
identity fields, and fill `reference_matches`, `unsupported_claims`,
`critical_misses`, `supported_outcome`, and evidence-based `review_notes`. Add
`reviewer_kind` at the document root as `human` or `ai`, and fill `reviewer` with
the reviewer's declared identity. A human label does not authenticate identity or
prove independence. Public reference matches are declared identifiers, not
verified findings or a recall denominator; references may include duplicates,
model-produced observations and false positives.

For an interrupted run, or to create a new blank sheet, select new output paths:

```bash
python3 benchmarks/public_host_review.py prepare \
  --receipt /absolute/private-run/receipt.json \
  --output /absolute/private-review/reviews.json

python3 benchmarks/public_host_review.py score \
  --receipt /absolute/private-run/receipt.json \
  --reviews /absolute/private-review/reviews.json \
  --output /absolute/private-review/report.json
```

The output parent must already exist; use a private directory controlled by the
owner. New files are created with owner-only permissions (`0600`), and existing
outputs or output symlinks are never overwritten.
Scoring the runner's original sheet uses the same `score` command with its path
as `--reviews`. Reordering entries is allowed; changing answer text, receipt
bytes, answer bytes, case/round identity, or duplicating/dropping entries is
refused. New `prepare` sheets add an opaque receipt-and-attempt digest so that
identical answers across both arms remain separately bound and scoreable. The
digest does not authenticate identity or prove blindness. The existing runner's
sheet has no such binding; it is accepted when case, round and answer hash select
one attempt unambiguously. If its two arms have byte-identical answers in the
same case and round, create a new `prepare` sheet and review its entries instead
of guessing which old judgment belongs to which arm. No current runner or
frozen candidate was changed for this tool.

Blank or partial judgments stay `PENDING`; missing values never become zero.
Completed judgments require notes and explicit reviewer identity/kind. A
supported outcome cannot contain counted unsupported claims or critical misses,
or belong to an attempt with a host error, missing answer, failed identity check
or incomplete recorded execution. The report retains started, completed,
reviewed and unstarted counts, and preserves the complete planned denominator.
It emits a supported-outcome fraction only for a complete, fully reviewed trial.
Reviewing every recorded attempt in a stopped run can yield `REVIEWED` while
`trial_complete` remains false and outcome fractions remain unknown.

Reported usage includes recorded failed attempts. Cached input remains a subset
of input, and missing counters are counted separately. Reported timing sums
retain missing-timing counts. Preflights, other runs, correction work, billing
and whole-task benefit are outside these sums. The report contains no answer
text or evidence notes, but its provenance and reviewer fields can still be
sensitive; review it before sharing.

The inputs are owner-selected local evaluation files, not an authenticated or
hostile-filesystem evidence system. Reads are bounded, refuse duplicate JSON
keys, nonfinite values, symlinked answer files/folders and hard-linked input
files, and use safe derived answer paths. Hashes bind selected bytes; they do
not attest the host, author, actual fixture execution, or reference quality.
All existing negative results and human-review gaps remain. No model/profile
qualification, route promotion, billed savings or unseen-case claim follows
from a successful report.

Synthetic regression checks:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p test_public_host_review.py -v
```
