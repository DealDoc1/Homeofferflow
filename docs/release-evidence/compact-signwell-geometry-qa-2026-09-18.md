# Compact SignWell geometry QA — September 18, 2026

## Purpose

Reduce provider requests and signer effort while completing the outstanding
provider-rendered geometry review for TXR-1501, TXR-1507, TXR-1905, TXR-1914,
TXR-1917, and TXR-1919.

This is a nonbinding test-only workflow. It does not change any production
recipient, signer plan, document, customer record, or application route.

## Local implementation and verification

`scripts/qa/build_compact_signwell_geometry_test.py` renders the six exact
private source forms into one synthetic packet. It retains every production
field's page-relative x/y/width/height, type, required state, and API ID. For
provider QA only, the semantic production roles are mapped to two synthetic
QA recipients using the owner's previously approved test addresses.

The resulting packet contains:

- 14 US Letter pages;
- 6 source-backed forms;
- 54 signature, date, or initials fields; and
- 2 parallel QA recipients.

Three focused tests pass. They independently verify form order, page offsets,
unchanged page-relative field geometry, unique field IDs, test mode, parallel
signing, disabled reminders, exact QA addresses, and failure on a missing
source.

All 14 unsigned pages were rendered with Poppler using a private writable font
cache and visually reviewed. A separate local image-only field-outline review
confirmed the shifted combined-packet coordinates remain on the intended
signature, date, and initials lines. No clipped content, missing form page, or
page-offset error was observed. QA images and the private-source packet remain
untracked under `tmp/pdfs/compact-signwell-geometry-20260918/`.

## Provider request

Exactly one SignWell request was created:

- document ID: `4ec37d4c-4283-4933-8416-28866c15f918`;
- name: `QA ONLY - corrected HomeOfferFlow signer geometry`;
- provider mode: test/nonbinding;
- signing order: disabled;
- reminders: disabled;
- recipients: `andrewchri@gmail.com` and `brewbqinfo@gmail.com`; and
- created at: `2026-09-18T23:21:00Z`.

Immediately before the request, SignWell displayed 2 of 25 included API
requests used for the billing period. The combined packet uses one request in
place of six separate form requests. The authenticated builder then confirmed
the document is **sent**, immutable, and contains all 14 document pages with
the expected signer fields.

The helper does not echo or persist the API credential. A saved local receipt
prevents accidental duplicate creation from the same output directory.

## Completed-provider review - September 21, 2026

Both QA recipients completed the existing document. The provider completion
email supplied the final PDF; no replacement document, reminder, or additional
API request was created.

- Completed PDF SHA-256:
  `59c9959922eb3cee8c6ca8c6c5de14c445817829670603201588a59c79f6e3e2`.
- The provider PDF is 14 US Letter pages, produced by HexaPDF, with no
  interactive form tree or JavaScript. Every page is marked as nonbinding test
  mode by SignWell.
- All 14 pages were rendered at 144 DPI and visually inspected. Every one of
  the 54 requested signature, date, and initials fields is completed. The
  fields remain on the intended source rules or footer blanks without clipping
  captions, crossing columns, or obscuring adjacent fields.
- TXR-1501 and TXR-1507 include both clients plus the associate alternative;
  complete dates remain readable inside their widened columns. TXR-1905,
  TXR-1914, TXR-1917, and TXR-1919 include both buyer and seller rows, and the
  page-one initials on TXR-1914 and TXR-1919 remain within their printed footer
  blanks.
- The prominent `Not Valid` artwork is the provider's expected test-mode
  watermark. It is not a production form field or a placement defect.

This completed provider evidence closes the outstanding geometry-review scope
for these six corrected forms. Both privacy-safe signing-map baselines were
refreshed from the reviewed field builders. The baseline refresh does not
change a field or source; it locks the reviewed geometry against future drift.

Thirteen focused geometry, map-review, and compact-packet tests pass against
the refreshed baselines. The complete repository suite also passes: 2,333
tests in 84.102 seconds.

No Vercel build/deployment, production database change, customer send, real
agreement replacement, cancellation, or reminder occurred during this review.
