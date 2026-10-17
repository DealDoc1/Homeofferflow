# Integrated seller-disclosure signing boundary

## Batch contract

- Outcome: verify the actual draft-to-signing boundary before a controlled
  integrated provider run, preserving real client packets.
- Scope: asynchronous tests of the existing seller-disclosure sender, existing
  draft/review/handoff regressions, and exact remaining evidence inventory.
- Production: e15c5db / READY dpl_47tztcZ7rgRmvVYvdCdLUubDpBSz, independently
  rechecked through the Vercel project this morning.
- Cost: no preview, application build, signing invitation, reminder, live draft,
  credential export, schema/permission change or paid service.
- Evidence: real sender invoked against fictional in-memory dependencies;
  integrated completed-provider PDF remains a separate requirement.

## Verified local behavior

The previous sender tests primarily asserted source markers and recipient
helpers. The new tests actually await _send_seller_disclosure_for_signature
and capture the payload delivered to its existing tracked-delivery boundary.
The renderer, database reads and delivery are mocked; source artwork is never
downloaded and no real PDF is generated or signed.

Twelve combinations cover one/two Sellers, zero/one/two Buyers, and optional
water disclosure. Checks preserve owner/draft/review filters, exact recipient
IDs/names, parallel signing, no extra signature page, packet bytes, source
identities, and the actual production field-builder result, including the
water-form page offset. The existing ordinary workflow requires completed
Seller review before sending; this checkpoint neither changes that workflow
nor claims Sellers can fill every disclosure answer inside SignWell.

Unavailable/unreviewed drafts, an existing untracked provider request,
invalid/missing/duplicate email addresses and failed source preview all stop
before delivery. No source/map/customer behavior is changed.

Focused command:

    python -m unittest tests.test_seller_disclosure_signing_boundary tests.test_seller_disclosure_draft_foundation tests.test_seller_disclosure_signing_path tests.test_seller_disclosure_agent_ui tests.test_seller_review_access tests.test_seller_review_api tests.test_listing_disclosure_handoff_runtime tests.test_seller_disclosure_feedback -q

Result: 43 tests in 0.414s, OK; whitespace passed. No full regression was run
for this test/evidence-only local checkpoint, and no application release is
needed. Independent CI and completed-provider review are not claimed.

## Current live and source inventory

- Live seller-workflow remains in_progress/partial. Source-specific sale and
  lease listing agreement workflows are not implemented; the shared catalog
  has no TXR-1101/1102 entry according to its current tracked evidence.
- A bounded filename search of the supplied iCloud HomeOfferFlow folder found
  seller_disclosure_notice_55-1.pdf and seller_water_disclosure_61-0.pdf, but
  no 1101/1102/1106 or listing-named source. No broad personal-folder scan.
  This is file availability, not a new licensing/source-owner approval gate.
- Read-only scenario/run search found only seller-financing and temporary-
  lease keys, no seller-disclosure-named scenario. This alone cannot prove
  no existing provider document or alternate-named test exists. Inventory
  existing fictional invitations/provider records before sending anything.
- Known amendment and showing tests remain pending final signer completion;
  this batch does not finalize their separate electronic disclosures.
- The older temporary checkout has 1,211 missing/changed paths. Preserved it
  unchanged and continued in an isolated Git worktree; production is unaffected.

Next bounded step: locate an existing fictional seller-disclosure provider
test or, if none exists, prepare a uniquely reserved controlled integration
case through the existing application connection. Do not substitute these
mocked tests for completed-provider field-placement evidence.
