# Seller source readiness verification - 2026-08-08

## Live source state

The production Supabase source table was checked read-only for the OnDemand
brokerage. The approved seller sources are present with authorization attested:

| Form | Revision | Status | Authorization | File |
| --- | --- | --- | --- | --- |
| TREC-55-1 | 05-04-2026 | approved | attested | seller_disclosure_notice_55-1.pdf |
| TREC-61-0 | 05-04-2026 | approved | attested | seller_water_disclosure_61-0.pdf |

## What this proves

- The exact private sources required for the seller-disclosure preview are
  available to the brokerage-scoped source-readiness flow.
- The source approval and authorization-attestation gates are satisfied.
- Local field-map and schema tests pass for both forms.
- The authenticated QA helper is configured for one- and two-seller previews,
  attaches TREC-61-0 when selected, and explicitly forbids sending/signing.

## What this does not prove

This verification does not activate seller-form sending. A live authenticated
one-seller and two-seller preview still must be downloaded and visually checked
for every populated field, response mark, signature line, signer role, and date
placement. Completed signed-PDF QA remains required before any seller-form
signing route can be enabled.

## Verification evidence

- Read-only Supabase query: `hof_brokerage_form_sources` for TREC-55-1/TREC-61-0.
- Targeted tests: 48 passed (`test_trec_seller_disclosure_map`,
  `test_trec_seller_disclosure_schema`, `test_authenticated_seller_qa`,
  `test_authenticated_txr_qa_helper`, and
  `test_brokerage_form_source_foundation`).
- No source bytes, storage paths, hashes, seller data, or signer data are
  included in this evidence file.

## Release status

Seller disclosure and seller-water workflows remain private preview/review-only
until authenticated point-of-use QA and completed-signature visual QA are
recorded. This is intentional.
