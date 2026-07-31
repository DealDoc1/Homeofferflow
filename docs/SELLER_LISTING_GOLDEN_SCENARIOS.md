# Seller/listing workspace golden scenarios

These scenarios validate the private seller/listing intake foundation only.
They do **not** approve, generate, download, or send a listing agreement,
seller disclosure, lease, or other legal form.

Use anonymous names and city/county-level context. Never place client names,
exact addresses, MLS numbers, or confidential notes in a shared QA record.

## Scenario SL-CAL-01 — Residential sale listing, two sellers

| Field | Value |
| --- | --- |
| Listing kind | Sale |
| Property context | Suburban resale; city/county only |
| Seller count | Two sellers |
| Requested workflows | Residential listing agreement — sale; seller disclosure |
| Agent expectation | Create a private intake workspace and keep seller/property details agent-private |
| Broker expectation | See only the aggregate sale/intake count; no names, address, notes, or form contents |
| Form expectation | Show source-readiness only; do not create or send TXR-1101 or TXR-1406 |

Review question: Does the workspace preserve the two-seller intake while keeping
source-gated form execution unavailable?

## Scenario SL-CAL-02 — Residential lease listing, one landlord

| Field | Value |
| --- | --- |
| Listing kind | Lease |
| Property context | Residential rental; city/county only |
| Seller/landlord count | One landlord |
| Requested workflows | Residential listing agreement — lease |
| Agent expectation | Create a private lease-listing intake workspace with no buyer-offer fields |
| Broker expectation | See only the aggregate lease/intake count; no landlord, address, notes, or form contents |
| Form expectation | Show source-readiness only; do not create or send TXR-1102 |

Review question: Does the lease path remain separate from purchase offers and
avoid implying that a lease listing agreement is available before source-owner
approval and completed signed-PDF QA?

## Required QA record

For each scenario, record:

- workspace created or rejected and why;
- requested workflow values persisted exactly;
- agent can read only the agent's own workspace;
- broker summary exposes aggregate counts only;
- source-readiness panel lists the relevant form code;
- no source PDF, form output, signer request, or download is exposed;
- any access-control or wording issue;
- disposition: pass, needs revision, or blocked pending source/QA.

## Release boundary

These scenarios do not authorize any seller/listing form release. The next
release gate still requires an authorized private source, a document-specific
data model, signer plan, rendered completed-PDF inspection, regression, and
HomeOfferFlow release-authority approval.
