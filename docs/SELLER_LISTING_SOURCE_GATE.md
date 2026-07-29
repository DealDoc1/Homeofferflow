# Seller/listing source gate

The brokerage form-source vault accepts the following listing-side codes only
as private, source-owner-authorized sources:

| Code | Intended future workflow |
| --- | --- |
| TXR-1101 | Residential listing agreement - exclusive right to sell |
| TXR-1102 | Residential listing agreement - exclusive right to lease |
| TXR-1406 | Seller's Disclosure Notice |
| TXR-1418 | Update to Seller's Disclosure Notice |

Uploading an authorized source does **not** make it available to agents,
generate a document, create a signature request, or permit source download.
Each workflow requires its own data model, recipient/signing plan, field map,
completed-PDF visual QA, and HomeOfferFlow release-authority approval before
it can be released. A customer organization must additionally attest only when
it owns the private source.
