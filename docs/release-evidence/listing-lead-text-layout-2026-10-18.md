# Listing lead explanations: actual overflow correction candidate

## Batch contract

- Outcome: Seller explanations stay readable inside their reserved answer
  area in the listing-side TREC 56-0 package.
- Scope: the unconnected listing lead renderer, its fixed fictional QA specimen,
  local preview and focused regression. Existing customer purchase packets,
  source TREC wording, signer/checkbox geometry and other forms are unchanged.
- Production baseline: `61e516d0a091646bbff14a00624051d4e328d4fc`; actual v1
  failed signer specimen `646c8e81-e9e9-4820-8774-e1a892cc661e` is retained.
- Cost: no new provider invitations or production deployment for this local
  checkpoint; do not repeat the full suite until the next coordinated batch
  is frozen. Preserve automatic Git deployments disabled.
- Required evidence: reproduced provider overflow, focused bounds/unchanged-
  source tests and changed-page local visual review; actual v2 provider font,
  completed signatures and PDF still need their own verification.

## Evidence and correction

The actual v1 signer displayed a 200-character fictional explanation in a
field that grew to 687px high instead of the reserved 73.333px. Conditional
required status and exact-one choices worked. No signature or disclosure
acceptance was attempted. Screenshot: chat output folder
`listing-lead-readback-2026-10-18/explanation-overflow.png`.

SignWell's current Create Document schema supports field height and fixed-width
wrapping, not an explicit font-size property. It documents that fixed width
allows text to display in multiple lines. Based on the **observed** provider
height/type-size coupling, the candidate starts text at one 18px line rather
than a paragraph-sized 73.333px field. It reserves a separate 95pt printed
answer region below the same top anchor. A one-paragraph, 200-character bound
prevents arbitrary manual-line-break growth; entered 4,000-character static
details and lossless continuations remain unchanged.

The local guide explicitly labels its 9.75pt font as a preview assumption, not
the provider's font. It no longer assumes a multiline answer must fit the
initial single-line input height. The ordinary single-Seller/broker and
two-Seller/associate explanation pages (2 and 4) were visually reviewed with
200 wide CJK characters: no overlap with headings, other answer regions or
initials. Source pages, known Unicode continuation, signatures and choice
locations are unchanged. The fixed QA revision advances to v2 and binds the
new layout digest `9ec04b6fd1e282f8f1e04a2d89d70c7468cb8fe75d19115f60cfa36e80e1d1bd`.
The reviewed-source pin is `0bc9f5d342b670df631d9dd478e53834fc68d010`, the
committed correction checkpoint. Updating that metadata pin does not change
the reviewed PDF content, fields or page images.

Official contract inspected: https://developers.signwell.com/reference/createdocument

## Status

Implemented locally; **38 focused checks pass**, including the unchanged
buyer lead-addendum packet path, and local changed-page preview is reviewed.
Not production deployed, not sent to either inbox, and not actual-provider
font/signature/PDF verified. Do not present this as customer listing activation
or a full Seller-suite pass. No new owner action is required for this code fix.
