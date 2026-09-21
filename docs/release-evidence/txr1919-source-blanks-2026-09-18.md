# TXR-1919 source blanks and initials - September 18

## Status

Local candidate only. No deployment, public push, provider request, customer
document replacement, or approved-map baseline refresh. This work follows the
placement defects found in the addenda execution-copy audit. TXR-1919 remains
standalone-only; combined-offer integration is not claimed complete.

## Source and corrections

The supplied two-page TXR1919.pdf is TREC 41-3, revision 11-07-2022, SHA-256
`048dfe44ddd32b2106fbc07189f410ba554defb30ba6ab072ac420eddb10b27f`.
The source has no canonical AcroForm fields and no widget annotations.

- Measured each credit-document, first/second loan, and variance-election
  checkbox independently. Six-point bold X marks now sit inside those cells.
- Moved the credit deadline, documentation, lender names, balances, payments,
  variance amount, assumption-fee caps, and interest-rate caps into the actual
  source blanks. Address placement is measured on both pages.
- Text fits at no smaller than seven points. If the complete answer cannot
  fit, the blank references an exhibit and a labeled continuation preserves
  the full entered answer. No financial term is inferred or abbreviated.
  Disabled loan answers and deselected other-document answers are omitted.
- Review-only party names remain absent from signing copies. Name overflow
  and continuation page counts are identical between review and signing.
- Added the previously missing page-one buyer/seller initials. Continuation
  initials follow the printed footer columns while retaining the standalone
  sequential recipient IDs, including one buyer plus two sellers.
- Updated the render and signing-map candidate revisions used by the existing
  internal delivery fingerprint. No additional end-user approval step added.
- The shared continuation header now accepts a complete property address;
  existing callers without that property retain their component-based address.

## Verification

- Focused renderer, source-boundary, party-clearance, and internal preview
  checks: 29 tests passed. Coverage includes both variance elections, all
  nonempty first/second-loan combinations, all credit-document marks, disabled
  terms, unbroken long lender names, long addresses and parties, review/signing
  parity, and one/two buyers and sellers.
- Generated three synthetic exact-source specimens: both loans/cash adjustment,
  second loan/sales-price adjustment, and long-answer continuation. Inspected
  all seven rendered pages. Printed entries and X marks fit their source blanks;
  execution regions contain no review-only names. Initials and signature
  outlines are QA aids, not actual provider-rendered handwriting.
- Private reproducible helper: `scripts/qa/txr1919_source_preview.py`. Source
  and QA PDFs stay untracked. It refuses an unexpected interactive source.
- Final full discovery: 2,122 tests in 35.852 seconds, 2,120 passed and two
  approved-map baseline tests failed. The source-calibrated set comparison
  reports both TXR-1507 changes and TXR-1919 initials; the second comparison
  stops at the first TXR-1507 mismatch. Log:
  `/private/tmp/hof-txr1919-source-suite-final.log`. These are not all-green
  results. Baseline tests were not rewritten to bless an unverified provider map.

## Remaining verification

Obtain completed-provider visual evidence before describing the candidate as
release-ready. The current approved-map comparison includes the earlier
TXR-1507 drift plus the added TXR-1919 initials; it is not merely an unchanged
TXR-1507 warning. No live signing completion was verified in this pass.

Separate source-blank correction work remains for TXR-1905 and TXR-1914.
