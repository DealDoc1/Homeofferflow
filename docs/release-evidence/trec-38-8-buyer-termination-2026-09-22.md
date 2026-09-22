# TREC 38-8 Buyer termination release evidence

## Release

- Release name: Guided TREC-38-8 Buyer's Notice of Termination of Contract
- Git commit / pull request: current `codex/trec-38-8-followup` release branch; pull request recorded after completed-provider QA
- Production scope: authenticated agent form library, purchase-document interview, private preview, and Buyer-only SignWell send
- Changed packet/form target marker: `TREC-38-8`

## Approved source

- Approved source form/template and version: Texas Real Estate Commission TREC No. 38-8, revision 02-10-2025
- Source owner: Texas Real Estate Commission official promulgated form
- Storage location (private only): `brokerage-form-sources/57f5c952-80af-4ba9-9f7f-ad99dcbc31c5/TREC-38-8-02-10-2025-bfb96295.pdf`; production source row `7eb07547-f418-4b4a-bc52-2b2aea1f1560`; browser clients receive catalog metadata, not a source URL
- Source SHA-256: `bfb9629540c101a2c5b924b2d9a956f3bd0c5370b348b1428a106873f75bb3ef`

## Authorization

- Authority to use this source: HomeOfferFlow product owner supplied the official source and directed public-form release for signed-in Texas agents
- Authorized reviewer: Andrew Christian, HomeOfferFlow product owner and counsel
- Date confirmed: 2026-09-22
- Authorized agent attestation: no per-agent or brokerage-seat attestation is required for this shared-library workflow; access remains authenticated and agent-role limited

## Signing plan

- Each recipient and role: one or two named Buyers; Seller names identify the contract parties but Sellers and the agent are not signing recipients
- Signing order: simultaneous (`apply_signing_order: false`) when two Buyers are included
- Broker oversight / visibility: the authenticated agent owns the private draft and confirms each Buyer recipient before sending; no broker signature is printed on TREC-38-8

## Rendered signed-PDF QA

- Completed packet evidence link or secure reference: pending one SignWell test-mode document after the account session is renewed
- Reviewer: Codex source/PDF review completed; completed-provider PDF review pending
- Every applicable blank, checkbox, initial, signature, and date visually reviewed: the unsigned source-backed QA PDF was rendered at 200 DPI. Property, Seller continuation, reason 1, reason 8, and the five-line other-provision answer are aligned. A first render exposed and corrected an invalid Buyer-name placement in the Seller continuation. The two Buyer signature and locked-date rectangles were overlaid and visually verified against the four printed execution blanks.
- Locked coordinates / known exceptions: completed-provider signatures and locked dates remain to be checked after both approved QA recipients sign; SignWell test mode is required and does not create a binding transaction

## Regression

- Dedicated golden scenario added: `tests/test_trec_38_8_followup.py`, covering Buyer-only recipients, parallel fields, selected termination reasons, the conditional other-provision answer, source text preservation, address autocomplete, and database/source allowlists
- Existing buyer-offer regression scenarios run: complete repository suite, including purchase packets, standalone signing, PWA, source-vault, and release-preflight coverage
- Test result / evidence: 2,452 tests pass; the exact official source and signing-map overlay were rendered and visually reviewed at 200 DPI

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer): Andrew Christian
- Approval date: standing release authority confirmed in the active HomeOfferFlow roadmap task
- Approved public-facing scope copy: “End a purchase contract” for a Buyer giving the Seller a termination notice under a selected contract or addendum provision
- Customer/brokerage source-owner attestation, if this source is private to that organization: not applicable; this is the shared official TREC source, not a customer-brokerage private agreement

## Deployment decision

- Ready for production: no; completed SignWell two-Buyer PDF placement QA is the sole remaining release check
- Rollback path: revert the release commit, redeploy the preceding production commit, retire the TREC-38-8 source row, and retain the additive database allowlist safely
- Post-deploy verification owner: HomeOfferFlow release QA
