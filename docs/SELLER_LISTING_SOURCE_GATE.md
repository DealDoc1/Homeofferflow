# Seller/listing source gate

The brokerage form-source vault accepts the following listing-side codes only
as private, source-owner-authorized sources:

| Code | Intended future workflow | Current supplied-source state |
| --- | --- | --- |
| TXR-1101 | Residential listing agreement - exclusive right to sell | Cataloged; exact source PDF still required |
| TXR-1102 | Residential listing agreement - exclusive right to lease | Cataloged; exact source PDF still required |
| TXR-1406 | Seller's Disclosure Notice | Cataloged; exact TXR source PDF still required |
| TXR-1418 | Update to Seller's Disclosure Notice | Cataloged; exact TXR source PDF still required |
| TREC-55-1 | TREC Seller's Disclosure Notice | Supplied PDF hash-verified against the approved source-vault revision; unsigned preview QA complete; signing release still gated |
| TREC-61-0 | TREC Seller's Disclosure About Groundwater and Surface Water Rights | Supplied PDF hash-verified against the approved source-vault revision; unsigned preview QA complete; signing release still gated |

Uploading an authorized source does **not** make it available to agents,
generate a document, create a signature request, or permit source download.
Each workflow requires its own data model, recipient/signing plan, field map,
completed-PDF visual QA, and HomeOfferFlow release-authority approval before
it can be released. A customer organization must additionally attest only when
it owns the private source.

The supplied and verified evidence is:

- seller_disclosure_notice_55-1.pdf, TREC revision 05-04-2026
- seller_water_disclosure_61-0.pdf, TREC revision 05-04-2026

The current source-vault records are:

- TREC-55-1: `49633253-590f-4c8d-b386-799df7f9ab3b`
- TREC-61-0: `df32675f-95a1-435c-b1c3-a8db1ed08b56`

Both sources have passed local unsigned preview QA using a two-seller,
two-purchaser sample. The previews confirm page order, response/check fields,
and signature-row placement without exposing source-storage URLs.

This is sufficient source evidence for continued implementation. It is not,
by itself, authorization to expose seller-side signing in production. The
remaining gate is authenticated QA with the intended seller recipients,
completed-PDF visual inspection, and release-authority approval.
