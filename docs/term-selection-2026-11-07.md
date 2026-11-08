# Request terms chosen by signal, and a wider walk

Status: development change in `0.4.0.dev18`, November 7, 2026, acting on the
two collector limits the [external recall run](external-recall-2026-11-07.md)
found binding on every real case. No model or host was run; the only numbers
are the collector's own file recall and span coverage.

## What changed

**Term selection.** The collector used to take the first sixteen words of the
request in order of appearance, after a small stop list. A long GitHub issue
therefore contributed its template ("system", "information", "describe",
"https", "github") and dropped the identifiers that followed. `request_terms`
now ranks every candidate word by signal and keeps the top sixteen:

- URL fragments are removed first (`https://…`, `www.…`).
- Words shorter than three characters, the old stop list and a template list
  (English function words plus issue-template vocabulary) never qualify. The
  template list deliberately leaves out `test`, `tests`, `error`, `failed`,
  `log` and `logs`, which name real things in code.
- Signal: a code-shaped word (an underscore or an inner capital) scores 3, a
  word containing a digit 1; a word in the request's first line scores 2 more;
  a word used more than once scores 1 more.
- Ties keep first-appearance order, so a one-line request, whose words all
  score alike, keeps exactly the order it had before. The cutoff
  `query_term_budget` is still reported when more than sixteen words qualify.

**Walk limits.** A 1,000-file walk took under half a second on the thirteen
external repositories, so the shipped default rises from 200 to 1,000 files
and 4,000 to 20,000 directory entries; the ceilings an operator may set rise to
5,000 files and 100,000 entries. The five-second deadline is unchanged and
remains the hard stop.

## Measured

**Task Lab.** 10/10 required spans, unchanged. **Four comparison fixtures.**
Decisive-file coverage identical to `dev17` (6/6, 6/7 plus one mapped, 6/6,
5/6 plus one mapped); their one-line tasks keep their word order, with the
template words `each`, `possible`-type prose no longer searched.

**Twelve self-commit cases** (the collector authors' own commits; direction
only): primary recall 12.9% → 15.2%, all excerpts 18.6% → 20.0%, cases with
any excerpted hit 9/12 → 10/12, per-case excerpted hits up 1, down 1, same
10. Recall including the map fell from 38.3% to 35.3% because template words
no longer match files everywhere, so the map is smaller and more specific.

**Thirteen Long Code Arena `dev` cases**, same cases and checkouts as the
November 7 external run:

| Run | Recall, primary four | Recall, all excerpts | Recall, with map | Cases reaching a changed file at any level | File-budget hits |
| --- | ---: | ---: | ---: | ---: | ---: |
| `dev17`, old terms, 1,000-file ceiling | 46.2% | 50.0% | 53.8% | 7/13 | 4/13 |
| `dev18`, new terms, 1,000-file default | 42.3% | 42.3% | 69.2% | 9/13 | 4/13 |
| `dev18`, new terms, 5,000-file ceiling | 46.2% | 46.2% | 76.9% | 10/13 | 0/13 |

Per case: keras and rich, missed entirely before, are now reached through the
map; streamlit is reached once its 1,410 files can all be walked; pipenv's
changed file dropped from an excerpt to the map; jax gained a primary hit. The
number of matching files fell sharply where template words had matched
everything (streamlit 993 → 165 of 1,410), which is what makes the map useful.
Walk time stayed under 1.4 seconds even for ccxt's 2,469 files. Three cases
(thealgorithms, ccxt, spacy) are still reached at no level.

## Reading

The change does what the external run asked: the request's identifiers now
reach the search, real repositories are walked whole, and the brief's map
points at the changed file in three more of thirteen real cases. Excerpt-level
recall did not rise, because the four primary windows still go to the files
with the most matching lines, which on a large repository are often
documentation or tests rather than the changed module; that is the next
thing to look at, and the 5,000-file ceiling makes it measurable on the whole
tree. Receipts are under `examples/receipts/term-selection-2026-11-07/`.

## Program checks

208 Python tests, four new: identifiers outrank template words and URL
fragments on a long issue, with a stable ranking; a one-line request keeps its
word order; URL-only and template-only requests are refused as before; and a
synthetic repository where the old positional terms selected template pages
now yields the changed module. Task Lab and the real-Chrome suites are
unaffected by the walk defaults in their fixtures.

## What this does not establish

- Anything on the unread `test` split or on repositories outside this sample.
- Answer quality or host turns; no model ran.
- That the template list is complete or harmless for every project; it is a
  fixed English list and is disclosed here so it can be reviewed.
