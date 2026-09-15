# Concurrent signing and accurate delivery status — September 15, 2026

## Scope and release authority

The owner requested simultaneous signing invitations instead of sequential
delivery. Standing release authority covers these implementation changes.
The existing morning report remains ACTIVE at 08:00 America/Chicago.

- All new standalone TXR agreements, reviewed seller disclosures, and production
  offer packets use `apply_signing_order: false`.
- Named recipients and their field assignments are unchanged. An included
  seller lease/addendum does not add seller acceptance fields to the purchase
  offer itself.
- The final update-and-send call uses an explicit list of supported options,
  omitting create-only fields such as `with_signature_page`. Reference:
  https://developers.signwell.com/reference/senddocument
- The offer success screen shows the buyer delivery address instead of the
  preparing agent's login email, and separates document email from signing
  invitation status. A failed signing attempt points to My Offers / Retry
  signing. A checkout return alone does not claim payment or packet completion.

## Approved source and authorization

Existing approved source PDFs, production source revisions, and source
authorization are unchanged. No new legal source or contract language is added.
Changed packet target: `api/fill-pdf.py`, production purchase offer / contract
packet delivery settings and invitation text only.

## Signing plan

All existing named signers receive invitations together and sign independently.
Existing recipient identities, signature/initial/date rectangles, page numbers,
required fields, source rendering, and field-verification checks are preserved.
The sent customer agreement recovered earlier today remains intact: SignWell's
sent-document UI did not permit editing its existing sending-order switch.
No replacement or duplicate customer invitation was sent for this change.

## Rendered signed-PDF QA

This change does not modify PDF rendering, legal terms, or field geometry.
Geometry regressions run with the full suite. No new completed-signature PDF
was generated or visually inspected for this delivery-only release. Prior
form-placement issues are not claimed resolved by these changes.

## Regression and verification

- Offline provider-contract tests execute create, persisted-field inspection,
  send, and saved sent status for both TXR-1507 and seller disclosure paths.
- Altering a persisted field prevents the send in both paths.
- Purchase-offer tests preserve buyer/seller recipient assignments while
  asserting concurrent invitations for included lease documents.
- JavaScript summary and DOM-state tests cover recipient selection, failed or
  disabled signing, concurrent signing, and unconfirmed checkout.
- Full regression result is recorded in the associated PR and release run.

## Known verification limits

The earlier production 422 send rejection was recovered by sending the existing
draft through SignWell and reconciling its HomeOfferFlow status. The provider
response body was not retained, so unsupported send options are a documented
contract mismatch, not a conclusively established cause of that specific 422.
The API contract correction is locally tested; no duplicate live customer
packet will be created to test it. Production deployment/HTTP checks do not
by themselves prove inbox receipt or a new end-to-end signed packet.

## Cost and rollback

No new service, subscription, deployment preview, or background polling is
introduced. Use the existing intentional prebuilt release after CI, with its
deployment-capacity check. Roll back the application artifact if needed;
already-sent SignWell documents and signatures are not modified by rollback.
