# Reuse a seller-signed disclosure in a purchase offer

## Outcome, scope and release authority

An agent or other preparing account can choose a completed, seller-only
HomeOfferFlow disclosure from the purchase attachment step rather than download
and re-upload it. The signed PDF copy, continuation/audit pages and source
artwork are appended without visual changes. The current offer's buyers receive
the already calibrated acknowledgment fields; sellers are not asked to sign
again. No unfinished disclosure is automatically required for other documents.

Owner standing authorization and release authority cover implementation, push,
merge and one intentional production release. Base is canonical production
`a162d1ea629b139e1e23689d6ed36e08ef959b70`, shell v108. Scope is the new saved
attachment component, existing owner-only status/download API, upload metadata
serialization and purchase composition. Unreleased TXR-1101/listing integration
and its migrations remain excluded. No real client record, subscription,
credential, source permission, email or signature invitation is changed for QA.
No new database migration or commercial service is needed. Automatic Git
deployments remain false. Shell v109 includes the new public component only;
private PDFs and API responses are never service-worker cached.

## Approved source and signing plan

Approved source is existing TREC-55-1 / optional TREC-61-0, revision 05-04-2026,
already authorized and registered. Source fingerprints are unchanged:
55-1 `65a52e167c290814930624ba230e232c152573359f1388cdb5e1237a62e4239a`,
61-0 `91056ab6520af8cbef319986e03490f1bf6947817c3d3f563348f80f957f871f`.

The signing plan imports the existing `trec_seller_disclosure.build_signwell_fields`
calibration, filters Buyer fields only, remaps them to current offer Buyers 1/2,
and offsets by the actual preceding PDF page count. No Seller fields are added,
no field goes on an audit page, and the original source/render maps are unedited.
The buyer receipt date remains 18px high, not the generic upload's smaller
default. Manual placement remains unchanged for other uploaded documents.

The API verifies the existing account session, queries the exact owner-scoped
draft, rechecks actual provider completion, rejects test-mode or mismatched
provider metadata, and returns the unchanged completed PDF plus a SHA-bound
layout description. Buyer-acknowledged copies are not silently signed again;
they can still be downloaded/attached using the existing manual workflow.
Property checks preserve unit information. Duplicate disclosures and existing
five-file / 2MB individual / 2.5MB combined limits remain enforced. No signing or
database write occurs while preparing this attachment.

## Rendered signed-PDF QA and regression boundaries

Rendered signed-PDF QA for the reused exact rectangles is the completed v4
disclosure test `b4ea4029-7e80-460c-880c-9e7275cee423`, both signers complete;
PDF SHA `3ba4969659936ce930501bfba2434f6870cab0ecd472b3cd8cbc2defedb45829`.
See `seller-disclosure-v4-completed-review-2026-10-19.md`. This is reused
component geometry evidence, not a newly completed combined purchase packet.

New actual-source local composition specimens cover one Buyer and two Buyers
with water rights. All appended pages, including audit placeholders, render
pixel-identically before/after real purchase composition. Visually reviewed the
four changed receipt/initial pages with calibrated field rectangles. A real
adapter test also places a survey and financing addendum before the disclosure,
preserves every marked fixture page and verifies both recipient IDs and offsets.
No provider completion or real seller signature is invented from these local
fixtures. A new live combined packet's completed-provider roundtrip is not
claimed by this release.

Focused frozen checks: 74 passed in 0.806s (composition, real API runtime,
ownership, duplicates/limits, payload metadata and PWA). One earlier command
listed a nonexistent checkout snapshot test module; that invocation failed as a
test-selection error, not a product result. The corrected frozen command passed.
Node syntax checks pass. Production column names verified with a zero-row SQL
probe; no customer data or direct table grants were requested.

## Browser -> API -> data -> response verification

Local browser fixture uses the real new component and real status API handler
with entirely fictional, read-only auth/database/provider responses. Matching
completed seller-only disclosure appears; pending and wrong-property records do
not. Selection adds exactly one attachment and explains automatic Buyer receipt.
Repeating selection reports already included without changing count. Holding a
response, closing the dialog and changing fictional account leaves zero attached.
The 390px picker is 358px wide with 356px scroll width; screenshot is in the chat
output folder `purchase-disclosure-reuse-2026-10-19/mobile-choice.jpg`.

Canonical post-deploy acceptance must verify the new entry point, owner-only
list/no-match behavior, current shell and runtime checks. Do not create a real
customer packet or another confusing QA stress bundle to claim acceptance.

## Release and cost boundary

Run exact-head CI once on the frozen candidate. Confirm fresh Vercel spending
headroom, then use the existing intentional prebuilt production workflow once.
No routine preview, new paid provider, schema migration or billing change.
Record actual PR, workflow, deployment and canonical outcomes below. The full
seller/listing roadmap remains in progress; unsigned disclosure plus listing or
purchase execution in a single request is separate from reusing a completed PDF.
