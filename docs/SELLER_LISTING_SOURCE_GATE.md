# Seller/listing source gate

The brokerage form-source vault accepts the following listing-side codes only
as private, source-owner-authorized sources:

| Code | Intended future workflow | Current supplied-source state |
| --- | --- | --- |
| TXR-1101 | Residential listing agreement - exclusive right to sell | Cataloged; exact source PDF still required |
| TXR-1102 | Residential listing agreement - exclusive right to lease | Cataloged; exact source PDF still required |
| TXR-1406 | Seller's Disclosure Notice | Cataloged; exact TXR source PDF still required |
| TXR-1418 | Update to Seller's Disclosure Notice | Cataloged; exact TXR source PDF still required |
| TREC-55-1 | TREC Seller's Disclosure Notice | Exact supplied PDF identified locally; source-vault upload and workflow QA remain separate |
| TREC-61-0 | TREC Seller's Disclosure About Groundwater and Surface Water Rights | Exact supplied PDF identified locally; source-vault upload and workflow QA remain separate |

Uploading an authorized source does **not** make it available to agents,
generate a document, create a signature request, or permit source download.
Each workflow requires its own data model, recipient/signing plan, field map,
completed-PDF visual QA, and HomeOfferFlow release-authority approval before
it can be released. A customer organization must additionally attest only when
it owns the private source.

The supplied local evidence is:

- seller_disclosure_notice_55-1.pdf, TREC revision 05-04-2026
- seller_water_disclosure_61-0.pdf, TREC revision 05-04-2026

These files are source evidence, not an authorization to activate seller-side
generation or signing.