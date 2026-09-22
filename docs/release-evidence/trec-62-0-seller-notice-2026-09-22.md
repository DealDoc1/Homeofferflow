# TREC 62-0 Seller notice release evidence

## Release

- Release name: Guided TREC-62-0 Seller Notice of Removal of Backup-Contract Contingency
- Git commit / pull request: current `codex/trec-62-followup` release branch; pull request recorded after creation
- Production scope: authenticated agent form library, purchase-document interview, private preview, and Seller-only SignWell send
- Changed packet/form target marker: `TREC-62-0`

## Approved source

- Approved source form/template and version: Texas Real Estate Commission TREC No. 62-0, revision 05-04-2026
- Source owner: Texas Real Estate Commission official promulgated form
- Storage location (private only): `brokerage-form-sources/57f5c952-80af-4ba9-9f7f-ad99dcbc31c5/TREC-62-0-05-04-2026-1d8a9afb.pdf`; production source row `61d46912-c383-4e59-bd04-78e54db09b18`; browser clients receive catalog metadata, not a source URL
- Source SHA-256: `1d8a9afb56b2dbe1c70ae9828943978f64d8bcfb6687ac45ab8788b13dd21b94`

## Authorization

- Authority to use this source: HomeOfferFlow product owner supplied the official source and directed its release for signed-in Texas agents
- Authorized reviewer: Andrew Christian, HomeOfferFlow product owner and counsel
- Date confirmed: 2026-09-22
- Authorized agent attestation: no per-agent or brokerage-seat attestation is required for this shared-library workflow; access remains authenticated and agent-role limited

## Signing plan

- Each recipient and role: one or two named Sellers; Buyer is identified in the notice but is not a signer; escrow-agent receipt sections remain blank
- Signing order: simultaneous (`apply_signing_order: false`) when two Sellers are included
- Broker oversight / visibility: the authenticated agent owns the private draft and confirms each Seller recipient before sending; no broker signature is printed on TREC-62-0

## Rendered signed-PDF QA

- Completed packet evidence link or secure reference: SignWell test-mode document `90de34ec-c2fe-443d-8bf9-651d5b7f74f3`, created 2026-09-22 for the two approved QA addresses
- Reviewer: Codex source/PDF review and completed signature visual QA
- Every applicable blank, checkbox, initial, signature, and date visually reviewed: the completed SignWell PDF was downloaded and rendered at 200 DPI; source-backed address, Buyer name, delivery date, both Seller signatures, and both locked signature dates are correctly aligned; both escrow-agent receipt sections remain untouched
- Locked coordinates / known exceptions: Seller signatures and locked signing dates sit above the two printed Seller rules; SignWell's test-mode `Not Valid` watermark is expected and is not present in live packets
- Authenticated QA: production point-of-use verification follows source upload and deployment; the current local interview, parser, renderer, recipient plan, and signing request are covered by focused tests

## Regression

- Dedicated golden scenario added: `tests/test_trec_62_0_followup.py`, including Seller-only recipients, parallel fields, source text preservation, address autocomplete, and database/source allowlists
- Existing buyer-offer regression scenarios run: complete 2,445-test suite run
- Test result / evidence: 2,445 tests pass; 218 focused form, signing, navigation, PWA, and release-preflight tests pass; source-backed PDF and geometry overlay visually reviewed

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer): Andrew Christian
- Approval date: standing release authority confirmed in the active HomeOfferFlow roadmap task
- Approved public-facing scope copy: “Remove a backup-contract contingency” for a Seller notifying the backup Buyer after the first contract has ended
- Customer/brokerage source-owner attestation, if this source is private to that organization: not applicable; this is the shared official TREC source, not a customer-brokerage private agreement

## Deployment decision

- Ready for production: yes; completed SignWell QA PDF, source vault record, database constraint, code, and regression suite are verified
- Rollback path: revert the release commit, redeploy the preceding production commit, retire the TREC-62-0 source row, and retain the additive database allowlist safely
- Post-deploy verification owner: HomeOfferFlow release QA
