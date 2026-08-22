# TXR-1905 private review draft release evidence

## Release

- Release name: TXR-1905 Mineral Reservation Addendum private review draft.
- Git commit / pull request: This release's dedicated commit and pull request record the implementation; the final commit identifier is recorded in the production release log after merge.
- Production scope: TXR-1905 only. Signed-in agents can complete a short interview and save a private, unsigned review PDF. No signature delivery, completed agreement, or source download is released by this change.
- Changed packet/form target marker: TXR-1905 / TREC 44-3 Addendum for Reservation of Oil, Gas, and Other Minerals.

## Approved source

- Approved source form/template and version: TXR-1905, TREC No. 44-3, revision 11-07-2022.
- Source owner: Texas Real Estate Commission promulgated form; the exact user-supplied PDF is retained as an approved private HomeOfferFlow source.
- Storage location (private only): HomeOfferFlow `brokerage-form-sources` private vault record for TXR-1905; no source URL is returned to agents.

## Authorization

- Authority to use this source: HomeOfferFlow product owner authorized the supplied TXR form library for all agent private-draft workflows on 2026-08-22.
- Authorized reviewer: Andrew Christian, HomeOfferFlow product owner and counsel.
- Date confirmed: 2026-08-22.

## Signing plan

- Each recipient and role: no recipients in this release. Buyer and Seller names render for a private review draft only.
- Signing order: not released; no signature request can be created by the TXR-1905 workflow.
- Broker oversight / visibility: the authenticated agent owns the private draft; source retrieval remains server-side and the existing private-draft list exposes no raw source PDF.

## Rendered signed-PDF QA

- Authenticated QA: an authenticated HomeOfferFlow brokerage-admin session uploaded and then confirmed the approved TXR-1905 source-vault record before this release; post-deploy authenticated agent-workspace QA remains part of release verification.
- Completed signature visual QA: not applicable to this release because the TXR-1905 signing route and signature fields are intentionally not released. No completed signed PDF is represented as tested or available.
- Rendered unsigned PDF QA: completed locally on 2026-08-22 against the exact approved TXR-1905 source. Address, the selected reservation checkbox, conditional undivided-interest percentage, selected surface-rights checkbox, and both buyer and seller printed-name areas were visually inspected.
- Reviewer: HomeOfferFlow release QA.
- Every applicable blank, checkbox, initial, signature, and date visually reviewed: every applicable unsigned blank and checkbox was reviewed. Initial, signature, and date fields are absent from this private-review release.
- Locked coordinates / known exceptions: no SignWell coordinate map is released; the source's signature rules remain unsigned.

## Regression

- Dedicated golden scenario added: `tests/test_txr_1905_renderer.py` covers one-page preservation and conditional reservation/surface-right overlays.
- Existing buyer-offer regression scenarios run: complete local automated suite.
- Test result / evidence: 1,093 tests passed locally on 2026-08-22; the exact-source rendered PDF was visually inspected.

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer): Andrew Christian.
- Approval date: 2026-08-22.
- Approved public-facing scope copy: the relationship workspace says this is a short guided TXR-1905 interview that saves a private review PDF and does not send or sign the addendum.
- Customer/brokerage source-owner attestation, if this source is private to that organization: approved private source is recorded in the source vault with authorization attestation; no agent-side access approval is required to start the private draft.
- Agent attestation: no agent attestation is required for this signed-in-agent private-draft workflow; authorization and source-vault attestations are server-audited.

## Deployment decision

- Ready for production: yes, for the narrow unsigned private-review scope only.
- Rollback path: revert the dedicated TXR-1905 release commit and redeploy the preceding verified production commit.
- Post-deploy verification owner: HomeOfferFlow release QA using an authenticated agent workspace.
