# Purchase-packet appraisal correction - September 18, 2026

**Local candidate, not deployed or completed-provider verified.**

The standalone appraisal correction did not affect the combined purchase-offer
renderer. This follow-on change unifies the source-blank layout while retaining
the purchase packet's Buyer-only appraisal execution scope.

## Changes

- Replaced the older fixed-position appraisal overlay with the existing
  TXR-1948 renderer. Selected amounts/days, Unicode addresses and checkbox
  appearances now match canonical editable field values.
- Namespaced appraisal fields under `hof_appraisal` during packet assembly.
  Interactive fields and their linked appearances remain intact. The original
  source PDF and any executed customer document are unchanged.
- Shared the standalone, source-calibrated Buyer signature rectangles. Removed
  the extra appraisal date fields because this source has no printed date
  blanks. Stable Buyer signature IDs are retained. No new Seller recipient is
  introduced, and both Buyers can still receive invitations together.
- Complete overlong answers continue on an attachment immediately after the
  appraisal form, with required initials for each invited Buyer on every
  added page. The Seller remains identified in the continuation header without
  being added to the signing request.
- Included continuation pages in subsequent addendum offsets. Missing selected
  appraisal source/continuation pages now produce an explicit generation/map
  error rather than silently omitting content or placing fields incorrectly.
- Preserved exact-source hash collection and recorded the reused renderer's
  revision in the purchase packet audit metadata. Synchronized production and
  staging renderer copies; no approved geometry reference was overwritten.

## Local verification

Regression coverage includes all three choices; canonical/widget/appearance
agreement; Unicode; one/two Buyers; unchanged short-packet page counts;
long-address continuations; following non-realty/HOA offsets; unsigned uploaded
attachments; missing-source/continuation rejection; cash/FHA/VA exclusion;
source hashes and render revision. Four offline production request cases use
real rendered packets and real field maps, intercepting only delivery. They
verify one delivery request, one combined file, matching fields, correct
recipient IDs and simultaneous invitations. These are not live email or
completed-provider checks.

`scripts/qa/purchase_appraisal_layout.py` produced three private QA specimens
from the repository's editable TREC 49-1 source. Four appraisal/continuation
pages were visually reviewed after Poppler rendering: waiver, partial waiver,
additional right and its full long-address continuation. The local blue boxes
show candidate field rectangles, not actual or simulated customer signatures.
The original source SHA-256 remains
`9cc7f9508a282830265dad72bdbef414afc3a78915c991b7e34d480d755e4b23`.

36 focused tests pass with bundled pypdf 6.10.0. Production-pinned pypdf 4.3.1
full suite: 2,272 tests in 54.519 seconds; 2,270 pass, with only the same two
pre-existing approved-geometry reference failures. The initial full run also
caught a staging/source synchronization mismatch; synchronizing the intended
changes resolved it before the final run. No reference fixture was changed.
Final local log: `/private/tmp/hof-combined-appraisal-final-suite.log`.

## Separate discovered issue and release boundary

The fifth reviewed page, the following HOA addendum, has correctly shifted
signature fields but its own fixed-width address overlay clips the deliberately
long address. This is not a passed whole-packet visual specimen; that renderer
needs a separate bounded-answer correction. The appraisal changes do not
claim to fix the HOA renderer or other existing purchase-page overlays.

The PDF skill required both canonical/appearance checks and actual rendered
inspection. No customer email, document, database row, provider request or
source PDF was changed. No public push or Vercel build/deployment was performed.
Cost/release constraints remain as documented in the live revalidation note.
QA scratch files are ignored under `tmp/pdfs/purchase-appraisal-review/`.
