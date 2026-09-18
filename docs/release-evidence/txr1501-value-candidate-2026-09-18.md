# TXR-1501 populated-value correction — September 18, 2026

**Local candidate; not deployed. No completed-provider verification in this turn.**
This follows the [execution correction](txr1501-execution-candidate-2026-09-18.md).
The same private 06-15-26 source was used; it and all customer documents remain
unchanged. No source PDF or client artwork is committed.

## What the expanded review found

The former QA helper inherited short-form sample data, leaving supported
long-form fields empty. Filling those areas revealed defects that its earlier
preview did not exercise:

- Pages 3-6 omitted the party-identification header; page 2 listed only clients
  and placed the header too low.
- Some contact values crossed or missed their rules. Term dates started before
  the blanks and could interfere with the printed sentence.
- The lease one-month percentage appeared after the percent sign; lease flat
  fee and retainer were outside their intended blanks.
- Protection days appeared inside paragraph text, not the days blank.
- The intermediary-authorized mark exceeded its cell and the no-intermediary
  mark was well above the intended checkbox.

## Local correction

All continuation headers now identify the supplied clients and brokerage on
the shared blank x=244.13..576.10, top-origin rule y=42.48. Font size is 8 points,
reduced only to 7 where needed. If complete names cannot fit, the header refers
to the parties identified in Paragraph 1; names are not silently truncated.
The primary party block retains the full supplied names.

Contact, term, percentage, flat-fee, retainer, protection-days and county values
are aligned with measured source blanks. Both intermediary marks, including
their stroke thickness, fit their source glyph cells. No fee calculation,
compensation selection, term wording, recipient or signature coordinate changed.
The correction prints the user's existing answers; it adds no interview steps.

The local preview helper now fills all those supported value areas and uses
different fee/retainer/intermediary choices across the two role specimens.
Values are synthetic QA examples, not recommended commercial terms.

## Verification

- 26 focused test methods pass: renderer, execution bounds, signer structure,
  continuation headers and populated-value bounds.
- Full discovery: 2,184 tests in 49.328 seconds; 2,182 pass, with only the same
  two approved signing-map reference comparisons failing. This is not an
  all-green result. Log: `/private/tmp/hof-txr1501-value-suite.log`.
- Four header tests cover one/two clients, brokerage-name fallbacks, whitespace,
  full-name retention and readable overflow references on all five continuation
  pages.
- New independent bounds cover 20 value regions and both intermediary choices.
  Running these two tests against the preceding committed renderer produced
  19 failing subcases with no test errors. They pass with the correction.
- Visually inspected all six associate-specimen pages. After the expanded
  fixture exposed defects, rerendered and reinspected all changed body pages
  (1-4), plus the alternative fee/retainer and no-intermediary pages in the broker
  specimen. Headers clear their labels; populated values clear their rules and
  surrounding text. The PDF skill required this visual review, not text-only QA.
- Private QA specimens and images remain untracked under
  `tmp/pdfs/txr1501-header-review/`. No provider sends, emails, charges, database
  writes, Vercel builds/deployments or public pushes occurred.

## Limits / next work

The two approved signing-map baseline mismatches remain separate from these
value/header changes. References were not regenerated to hide pending review.
Completed SignWell behavior remains unverified for the long-form candidate.

Follow-up: pages 1-5 now have local footer-initial coverage, source-bound tests
and rendered review; see [initials evidence](txr1501-initials-candidate-2026-09-18.md).
Completed-provider review remains unverified; full signing completeness is not
claimed. Extreme-length primary names/contact/market-area answers also need a
separate fit/continuation review; header overflow protection does not solve every
free-text area. These are local follow-ups, not requests for user approval.
