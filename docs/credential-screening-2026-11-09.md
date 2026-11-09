# Credential screening before you share a brief

Recorded November 9, 2026 for `0.4.0.dev25`. This is a first, warn-only step
on TODO item 8 (private-data handling). It does not close that item.

## The gap

A brief is meant to be pasted into a cloud assistant. Until now, the only
protection was the collector's refusal of known secret file names, such as
`.env`, `id_rsa` and `credentials.json`. A token hard-coded in an ordinary
source file, a log or the request itself went into the brief without notice.

## What it does now

After every preparation, `screening.py` scans everything the brief can share:

- the original request;
- every exact excerpt;
- the first lines of mapped files;
- the line index texts.

It looks only for formats with a distinctive prefix or structure:

- private key blocks;
- AWS access key IDs;
- GitHub, GitLab and Slack tokens;
- Google API keys;
- Stripe live keys;
- Anthropic and OpenAI API keys;
- JSON web tokens;
- password or secret assignments with a literal of eight characters or more.

Visible placeholders such as `changeme`, `${VAR}`, `<your key>` and `example-…`
are ignored. Generic high-entropy detection is deliberately left out, because
it fires on hashes and test data.

Each finding gives the kind, the place (the request, an excerpt, the map or the
line index), the path and line, and a masked preview of the first four
characters and the length. The secret itself is never shown or repeated. At
most twenty findings are reported.

## Where you see it

- **Workbench:** a notice above **Copy brief** lists the findings. It is never
  added to the copied text, the text download or the brief.
- **CLI:** `brief` and `assist` print the same lines to standard error, so
  standard output stays the exact brief.
- **JSON:** `--format json` and the helper's result carry the findings under
  `screening`.

## What it deliberately does not do

- **It does not remove or rewrite anything.** Exact source stays exact, as the
  project's rules require. If a finding is real, remove the secret from the
  file or edit the copied text before sending, and rotate the credential.
- **It does not block sharing.** Blocking, or a confirm step before copying, is
  a product decision for the owner.
- **No finding does not mean safe.** Unknown token formats, secrets split
  across lines and private non-credential data such as customer names are not
  detected.
- **The local model sees unscreened text.** It runs on this PC over loopback.

## Checks

- **Python tests:** six new tests in `tests/test_screening.py` cover each
  format, placeholders and ordinary code that must not fire, masking, the
  excerpt line number, a finding in the request, the CLI's stderr-only warning
  and silence for clean source. Fixture credentials are assembled at runtime,
  so no file in the repository holds a literal token.
- **Workbench:** a clipboard test checks that the notice appears and that
  neither the preview nor the copied text contains it. It also checks that
  malformed findings are dropped.
- **All suites:** the Python suite, the node clipboard suite and all eight
  browser suites pass.
- **Headless pass:** with a synthetic key in a throwaway project, the notice
  showed above Copy at 1280 and 390 pixels with no overflow and no console
  errors.
- **False-positive rate:** on the 61 real repositories from the recall work,
  one brief was flagged. The flag was a password literal in that issue's own
  request text, and no repository source fired.

Writing the tests caught three pattern defects before shipping:

- an Anthropic key was also reported as an OpenAI key;
- `DB_PASSWORD = "…"` was missed because of a word boundary after `_`;
- a hyphenated placeholder was not recognised.
