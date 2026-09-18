# Lease-addendum answer placement and continuations - September 18, 2026

## Status and scope

Local candidate for TXR-1953 (Residential Leases) and TXR-1954 (Fixture Leases),
using the privately supplied 11-07-2022 one-page source editions. Each source
was inspected for canonical fields/widgets and has none. Overlaying the blank
source is appropriate; no executed document was edited or re-exported.

No Vercel build, deployment, GitHub push, provider document creation or email
send occurred. Source PDFs, source hashes, synthetic QA specimens and images
remain local in ignored QA storage, not in this repository's published files.

## Findings and changes

- Fixed-height continuation canvases could place answers below the page or
  beyond its right edge, especially for long unbroken identifiers. Both forms
  now use the existing Unicode-aware, lossless paginated continuation layout.
- Address, preview names, oral notices, explanation and other-fixture entries
  now fit their actual printed blanks, or refer to a full-text exhibit.
- TXR-1954 oral notices use both source lines, starting above the first rule.
  Short notices can now stay on the original page rather than unnecessarily
  producing an attachment. Assumed-fixture and first-cost baselines also align
  with their source rules.
- TXR-1953 explanations use the first short source blank and following full
  lines. Assignment-only answers are omitted when termination is selected;
  inactive oral-notice and other-fixture answers do not leak into the form.
- Signing copies omit preview names from the signature lines. Long names are
  preserved in the exhibit, so draft and signing copies have identical
  continuation counts and the same initials map.
- Every continuation has required initials for the actual one-or-two Buyers
  and one-or-two Sellers. Standalone IDs remain sequential; combined purchase
  packets retain the reserved Buyer IDs 1/2 and Seller IDs 3/4.
- Existing base-page signature rectangles and checkbox centers are unchanged.
  No new brokerage seat, source-owner approval or preparation requirement was
  introduced. Invitations remain simultaneous.
- Rendering revisions and signing-map metadata were advanced so recovery
  fingerprints distinguish the new generated contents from earlier copies.

## Verification

Independent PDF-glyph tests check horizontal bounds and clearance above the
source rules, including property, day count, explanation, oral notice, fixture,
cost and all four preview-name positions. Long-value tests preserve every term
at the saved-interview limits, including Unicode names and literal markup,
without changing the input data or drawing outside the page.

Actual offline standalone render-and-send tests cover both forms, short/long
answers and all four Buyer/Seller count combinations (16 scenarios). They
verify one source download, one provider send, exact recipients, field maps,
rendered page counts and simultaneous invitations. These use a mocked network;
they are not evidence of live email delivery or completed SignWell signatures.

Combined purchase-packet tests cover both long-answer addenda together, all four
Buyer/Seller count combinations and a final uploaded document. They verify
every continuation's page offset and recipient, the final upload position,
unique field IDs and current renderer revision metadata.

Four synthetic source-backed signing-field review specimens were rendered
with production-pinned pypdf 4.3.1 and inspected with Poppler: ordinary
TXR-1953 (1 page), long TXR-1953 (3), ordinary TXR-1954 (1), long TXR-1954 (3).
All eight pages were visually inspected, including source answer lines,
unobstructed signature areas, repeated exhibit identification, pagination,
Unicode/literal input and each initials footer. Colored field outlines are
local review aids, not actual provider-rendered signatures.

Focused regression suite: 66 tests passed with both the bundled runtime and
production-pinned pypdf 4.3.1. Full production-pinned suite: 2,259 tests in
51.512 seconds, 2,257 passed and the same two pre-existing approved-geometry
baseline tests failed. No additional failures were introduced. The local log
is `/private/tmp/hof-lease-addenda-final-suite.log`.

## Outstanding release work

This candidate is not deployed. Existing completed-provider evidence from
September 15 covers older one-Buyer/one-Seller base pages only, not these new
continuations or two-party variants. Those narrower results are not promoted
to a full pass. The two pre-existing approved-geometry baseline disagreements
for other forms must remain visible rather than rewriting approval fixtures
to match unverified candidates. Current release-spending and migration
dependencies remain as documented in the live release revalidation record.
