# TXR-1953 private review release evidence

## Release

- Release name: TXR-1953 residential-lease addendum private review draft
- Git commit / pull request: PR #907 (TXR-1953 guided review workflow)
- Production scope: signed-in agent relationship workspace, private unsigned PDF preview only
- Changed packet/form target marker: TXR-1953 residential lease addendum

## Approved source

- Approved source form/template and version: TXR-1953 / TREC 51-1, revision 11-07-2022, `TXR1953.pdf`
- Source owner: platform-wide approved source catalog; no brokerage-specific source owner is required for this shared workflow
- Storage location (private only): Supabase `brokerage-form-sources` private source vault; approved row verified for TXR-1953

## Authorization

- Authority to use this source: approved shared HomeOfferFlow source catalog
- Authorized reviewer: platform-admin source-vault record with `authorization_attested=true`
- Date confirmed: 2026-08-24
- Agent attestation: the workflow is available to signed-in agents through the shared catalog; each agent remains responsible for the source-form review and brokerage process before any separate signature action

## Signing plan

- Each recipient and role: none; this release is a private review draft and does not create recipients
- Signing order: not applicable; signing is not enabled for TXR-1953
- Broker oversight / visibility: agent reviews the saved PDF privately through the signed-in workspace

## Rendered signed-PDF QA

- Completed packet evidence link or secure reference: authenticated preview QA completed from the approved source; rendered artifact `/private/tmp/txr1953-filled.pdf` used for visual inspection
- Reviewer: HomeOfferFlow release reviewer
- Every applicable blank, checkbox, initial, signature, and date visually reviewed: yes; lease-status and delivery checkboxes, delivery-day/oral-notice fields, property line, explanation area, and four signature lines were checked against the source; completed signature visual QA is not applicable because no signature request or signed-PDF workflow is enabled
- Locked coordinates / known exceptions: source signature fields remain blank by design; overlay coordinates are covered by `lib/txr_1953.py`

## Regression

- Dedicated golden scenario added: `tests/test_txr_1953_renderer.py` and parser/UI coverage in `tests/test_standalone_agreement_foundation.py`
- Existing buyer-offer regression scenarios run: full test suite
- Test result / evidence: full regression suite passed; rendered one-page visual QA passed

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer): HomeOfferFlow product release process
- Approval date: 2026-08-24
- Approved public-facing scope copy: every signed-in agent can start a private TXR-1953 residential-lease draft from the shared library; it does not provide legal advice, send, or sign the addendum
- Customer/brokerage source-owner attestation, if this source is private to that organization: not applicable to the platform-wide approved source catalog

## Deployment decision

- Ready for production: yes
- Rollback path: revert the PR and redeploy the prior production deployment
- Post-deploy verification owner: HomeOfferFlow release process
