# TXR-1507 answer placement and continuation - September 18, 2026

**Local candidate. Not deployed, sent or completed-provider verified.**

## Source and findings

Inspected the supplied two-page 06-15-26 source, SHA-256
`ff3c3682f68036d502314ca6bb2230c28d8e0b1ca5a4a5d4816a66f9f415b46f`.
The executed client document was not changed or used as an editable template.

The old lease-one-month percentage started at x=231, while its actual blank is
x=137.66..180.02. Total-rents percentage started at x=385 instead of its
312.65..360.07 blank. Lease flat fee was on the wrong line. Purchase flat fees
started near the end of their blank and could overprint the following period.
Term dates and the showing-fee text descended below their source rules. Long
names and market-area text were not bounded by their actual available spaces.

## Correction

All supported answer placements now use measured blanks. The three market-area
lines and two client-name blanks are used where needed. Text never shrinks below
7 points. Answers that still do not fit are referenced in the source blank and
copied in full to a clearly titled answer continuation. Unicode and literal
markup use the existing font-safe renderer; terms are not inferred or changed.

The continuation reuses the long-form layout with a short-form title, page offset
and unique field IDs. Headings stay with their answers rather than being stranded
on the preceding page. Each appended page receives required initials from the
same selected client(s) and broker/associate. No extra signer is added.

The server and local preview helper derive continuation fields from the actual
rendered page count. The dormant live-test helper is updated likewise, but was
not run. The unpublished signing-map identifier is
`txr-1507-2026-09-18-answer-continuation-candidate-v3`. Existing stale-copy checks
apply. Base signature/date/initials coordinates and role checkboxes are unchanged
from the prior candidate; this does not extend historical provider QA to new
continuation pages or to previously untested signer combinations.

## Verification

- 64 focused test methods pass across short-form answer/source bounds,
  execution, renderers, long-form continuations, server dispatch and delivery.
- Final full discovery: 2,205 tests in 50.516 seconds; 2,203 pass and the same
  two approved signing-map reference comparisons fail. Log:
  `/private/tmp/hof-txr1507-answers-final-suite.log`.
- New independent source-bound tests cover all compensation alternatives,
  showing fee, dates, printed names and license values. Against the preceding
  committed renderer, two test methods expose six placement failures.
- Long-answer tests preserve complete names and market-area text, including
  unbreakable strings, accented names, non-Latin text and literal markup.
- Actual-render/actual-delivery-adapter offline tests cover one/two clients and
  both professional roles. Every appended page reaches the simulated provider
  with the correct required initials. No live API was invoked.
- Four private synthetic PDFs were generated from the source: ordinary and
  long answers for both broker and associate. All 12 pages were rendered and
  visually reviewed. The PDF skill's visual pass caught an orphan heading;
  it was fixed, rerendered and regression-tested. These are synthetic geometry
  previews, not actual signed documents.
- QA outputs remain private and untracked under
  `tmp/pdfs/txr1507-answers-review/`.

## Outstanding

Completed-provider review remains necessary for the new continuations and all
unverified signer variants. The two existing approved-reference-map comparisons
remain visible; no approved baseline was regenerated. This does not claim full
transaction readiness or production deployment.

No push, build/deployment, live send, customer email, reminder, database mutation,
paid test or new resource occurred. Existing source and signed documents remain
unchanged. No new customer-facing gate, brokerage-seat requirement or approval
step was introduced.
