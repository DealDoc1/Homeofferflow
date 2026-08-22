# TXR-1914 private seller-financing review draft release evidence

## Release

- Release name: TXR-1914 Seller Financing Addendum private review draft.
- Git commit / pull request: recorded by this release's dedicated merge and production deployment.
- Production scope: TXR-1914 only. Signed-in agents may complete a conditional interview and save a private, unsigned review PDF. This release does not create loan documents, send, or sign the addendum.
- Changed packet/form target marker: TXR-1914 / TREC No. 26-8 Seller Financing Addendum.

## Approved source

- Approved source form/template and version: TXR-1914, TREC No. 26-8, revision 11-07-2022.
- Source owner: Texas Real Estate Commission promulgated form; the exact user-supplied PDF is retained as an approved private HomeOfferFlow source.
- Storage location (private only): HomeOfferFlow `brokerage-form-sources` private source vault record for TXR-1914; no source URL is returned to agents.

## Authorization

- Authority to use this source: HomeOfferFlow product owner authorized the supplied TXR form library for all agent private-draft workflows on 2026-08-22.
- Authorized reviewer: Andrew Christian, HomeOfferFlow product owner and counsel.
- Date confirmed: 2026-08-22.

## Signing plan

- Each recipient and role: no recipients in this release. Buyer and Seller names render for a private review draft only.
- Signing order: not released; no TXR-1914 signature request can be created by this workflow.
- Broker oversight / visibility: an authenticated agent owns the private draft; the source is retrieved server-side and the saved-drafts list never exposes the raw source PDF.

## Rendered signed-PDF QA

- Authenticated QA: the approved TXR-1914 source-vault record was verified in the authenticated HomeOfferFlow environment before this release.
- Completed signature visual QA: not applicable to this release because no TXR-1914 signing route or signature fields are released. No completed signed PDF is represented as tested or available.
- Rendered unsigned PDF QA: completed locally on 2026-08-22 against the exact approved two-page source. Address, credit-documentation days and choices, note amount, interest rate, conditional payment-plan fields, property-transfer choice, casualty-insurance choice, escrow choices, and buyer/seller printed-name areas were visually inspected.
- Reviewer: HomeOfferFlow release QA.
- Every applicable blank, checkbox, initial, signature, and date visually reviewed: every applicable unsigned blank and checkbox was reviewed. Initial, signature, and date fields are absent from this private-review release.
- Locked coordinates / known exceptions: no SignWell coordinate map is released; source signature rules remain unsigned.

## Regression

- Dedicated golden scenario added: `tests/test_txr_1914_renderer.py` verifies two-page preservation and conditional review-value overlays.
- Existing buyer-offer regression scenarios run: complete local automated suite before production release.
- Test result / evidence: local focused renderer and standalone-draft tests passed on 2026-08-22; exact-source rendered PDF was visually inspected.

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer): Andrew Christian.
- Approval date: 2026-08-22.
- Approved public-facing scope copy: the relationship workspace says this is a conditional source-form interview that saves a private review PDF and does not recommend terms, create loan documents, send, or sign the addendum.
- Customer/brokerage source-owner attestation, if this source is private to that organization: the approved private source is recorded in the source vault with authorization attestation; no agent-side access approval is required to start the private draft.
- Agent attestation: no agent attestation is required for this signed-in-agent private-draft workflow; authorization and source-vault attestations are server-audited.

## Deployment decision

- Ready for production: yes, for the narrow unsigned private-review scope only.
- Rollback path: revert the dedicated TXR-1914 release commit and redeploy the preceding verified production commit.
- Post-deploy verification owner: HomeOfferFlow release QA using an authenticated agent workspace.
