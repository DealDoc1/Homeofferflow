# Seller financing and mineral reservation placement - September 18

## Status

Local candidates only, not deployed and not completed-SignWell evidence. Both
forms remain standalone; this does not complete their combined-offer workflow.
No real customer document, external account, or approved-map baseline changed.

## Source checks

Read the supplied originals, extracted printed rules and checkbox cells, and
checked both canonical fields and page widgets: neither source is interactive.

- TXR-1905 / TREC 44-3, 11-07-2022, one page. SHA-256:
  `79f6b8e8b4faa8293abddf4e298f39dbaada703919812c01726c9721af5b0cf3`.
- TXR-1914 / TREC 26-8, 11-07-2022, two pages. SHA-256:
  `a331f1fab915b749639895fb6083c17291cd0964f4cf6327480c54f6dcffd9f9`.

## Corrections

- Repositioned all checkbox marks to their specific source cells. Financing
  funds verification was previously assigned x=189 instead of its x=245..256
  source cell. Consent-not-required appeared below its actual option. Several
  other marks touched a border or sat above it.
- Repositioned financing interest percentage from the middle of printed text
  to the small blank at x=78.96..105.42. Corrected all note/payment, timing,
  credit-document, and address blanks across both pages and all three plans.
- The interview collects months, but the due/start blanks do not print a time
  unit. They now include the entered number plus "month"/"months". Blanks with
  an existing printed unit keep only the number. Mineral percentages now
  explicitly include "%"; its source blank otherwise has no unit.
- Inactive options do not leak stale answers. Missing/invalid enumerated choices
  no longer silently select a payment plan, insurance, escrow, reservation,
  or surface-rights option. Existing API validation remains unchanged.
- Shared lossless text layout fits at no less than seven points or appends a
  labeled continuation. Long addresses, names, and documentation are preserved
  without abbreviating entered terms. The same continuation pages are used in
  review and signing copies. Review-only names never cover execution artwork.
- Seller-financing buyer signature fields began at PDF x=41.25, left of their
  x=55.44 source lines. Both columns now fit their rules. First and second
  rows finish above, not across, the rules. Added missing page-one initials.
- Mineral seller fields extended past their line ends and second-row fields
  crossed the line slightly. Narrowed/moved those candidate fields into bounds.
- Continuation initials preserve sequential standalone recipient IDs while
  using the correct printed buyer/seller columns, including one buyer/two
  sellers. Internal render/map revisions identify the new output without a
  new end-user reapproval step.

## Evidence

- Ran the six new source-boundary methods against the prior HEAD implementation
  in isolated in-memory modules: 12 failing methods/subcases, zero errors.
- Expanded focused run: 67 tests passed. Tests cover seven payment variants,
  all 20 combinations of transfer/insurance/escrow choices, four mineral choice
  pairs, exact selected-cell containment, every active source answer, units,
  one/two buyers and sellers, execution bounds, and lossless overflow.
- Rebuilt seven exact-source synthetic specimens with field outlines and
  visually inspected every page: 13 pages total, including long-answer
  continuations. Corrected ordinary entries are legible, selected X marks sit
  inside their cells, and the execution fields clear printed captions. These
  outlines do not prove how completed SignWell signatures will render.
- Reproducible private helper: `scripts/qa/txr_financing_mineral_preview.py`.
  It refuses unexpected interactive sources. Source and QA PDFs stay untracked.
- The first full run found old exact-position assertions and an outdated
  default-revision expectation in addition to the two approved-baseline
  failures. Updated the ordinary unit checks to assert the measured source
  boundaries/current revision. Approved baseline fixtures remain untouched.
- Final full discovery: 2,128 tests in 36.185 seconds; 2,126 passed and two
  approved-map baseline tests failed. Log:
  `/private/tmp/hof-financing-mineral-suite-final.log`. Not an all-green suite.

## Remaining work

Completed-provider PDF visual verification is still required for the changed
signature/initials maps before claiming release readiness. The approved-map
comparison now includes TXR-1507, TXR-1919, TXR-1905, and TXR-1914 differences.
This is not an unchanged or solely TXR-1507 warning. Combined-offer integration
and authorized production release remain separate unfinished work.

No signing invitation, public push, Vercel build, or deployment was triggered.
