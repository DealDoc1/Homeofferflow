# Seller's Temporary Residential Lease - production release evidence

## Release

- Release name: Seller's Temporary Residential Lease production execution
- Git commit / pull request: Release commit on `release/safe-platform-batch`
- Production scope: TREC 15-7 Seller's Temporary Residential Lease only.

## Approved source

- Approved source form/template and version: TREC 15-7 Seller's Temporary Residential Lease, 11-03-2025.
- Source owner: Texas Real Estate Commission promulgated form retained in HomeOfferFlow's approved form source.
- Storage location (private only): repository deployment asset; completed packet remains outside source control.

## Authorization

- Authority to use this source: HomeOfferFlow product release authorization after completed signing QA.
- Authorized reviewer: Andrew Christian, HomeOfferFlow CEO.
- Date confirmed: 2026-07-29.

## Signing plan

- Each recipient and role: Buyer 1 and optional Buyer 2 sign as Landlord; Seller 1 and optional Seller 2 sign as Tenant.
- Signing order: Buyer/Landlord recipients first, then Seller/Tenant recipients.
- Broker oversight / visibility: generated offer record remains available through the existing authorized brokerage workspace.

## Rendered signed-PDF QA

Completed packet evidence: retained signed staging packet is outside the repository because it includes test-signer information.

Reviewer: Andrew Christian with HomeOfferFlow visual QA review.

Every applicable blank, checkbox, initial, signature, and date visually reviewed: yes.

Locked coordinates / known exceptions: Effective Date intentionally remains blank for broker completion after final acceptance.

### Completed-packet result

| Packet page | Audit item | Result |
| --- | --- | --- |
| 6 | Paragraph 10A possession election | Seller temporary lease selected; Buyer temporary lease blank. |
| 9 | Paragraph 22 lease checklist | Seller's Temporary Residential Lease selected; Buyer lease and unrelated addenda blank. |
| 10 | Main contract execution | Both Buyer and both Seller signatures/dates sit on their corresponding execution lines; Effective Date remains blank. |
| 13 | TREC 15-7 parties and terms | Buyers render as Landlords; Sellers render as Tenants. Address, termination date, daily rent, deposit, utilities, pets, and special provisions are readable in their printed areas. |
| 13 | TREC 15-7 initials | Both Landlord and both Tenant initials appear on their respective printed lines. |
| 14 | TREC 15-7 holdover and notices | Holdover amount and Landlord/Tenant notice contacts render in their intended blanks. |
| 14 | TREC 15-7 signatures | Both Landlord and both Tenant signatures sit on their intended lines without body/footer overlap. |
| Entire packet | Ordering and count | 14 pages; no unrequested finance or lease addendum is present. |

## Regression

- Dedicated golden scenario added: four-recipient Seller Temporary Lease staging scenario and production SignWell recipient-order test.
- Existing buyer-offer regression scenarios run: full local suite plus the eleven-scenario rendering baseline.
- Test result / evidence: 188 tests passed locally on 2026-07-29. The Seller Temporary Lease golden rendering matches its approved baseline.

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer): Andrew Christian.
- Approval date: 2026-07-29.
- Approved public-facing scope copy: the offer interview describes the form as a Seller's Temporary Residential Lease and makes clear that Buyer signs as Landlord first and Seller signs as Tenant afterward.
- Customer/brokerage source-owner attestation, if this source is private to that organization: not applicable; this is a state-promulgated form held in HomeOfferFlow's approved source set.

## Deployment decision

- Ready for production: yes.
- Rollback path: revert this release commit and redeploy the immediately preceding verified production commit.
- Post-deploy verification owner: Andrew Christian and HomeOfferFlow release QA.

## Release decision

The four-recipient layout passed rendered completed-PDF inspection. Production
implementation must require distinct Seller/Tenant routing details and preserve
the signer order: Buyer/Landlord recipients first, then Seller/Tenant
recipients. The test-only staging allowlist and `sellerExecutionTestMode` are
not part of the production route.
