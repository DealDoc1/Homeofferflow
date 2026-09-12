# TXR-1507 completed-signature offset correction — September 12, 2026

## Release

- Release name: TXR-1507 Short Form completed-signature offset correction
- Git commit / pull request: pending the release commit
- Production scope: corrective electronic-signature and date placement for
  `TXR-1507 Residential Buyer/Tenant Representation Agreement - Short Form`.
  It changes neither the source edition nor agreement terms, recipients, or
  interview.
- Changed packet/form target marker: TXR-1507

## Approved source

- Approved source form/template and version: private TXR-1507, revision
  06-15-26.
- Source owner: HomeOfferFlow-authorized Texas form archive.
- Storage location (private only): HomeOfferFlow source vault.

## Authorization

- Authority to use this source: existing HomeOfferFlow production authority.
- Authorized reviewer: HomeOfferFlow product owner.
- Date confirmed: September 12, 2026.

## Signing plan

- Each recipient and role: one or two Clients plus the selected Broker or
  Broker's Associate.
- Signing order: selected Broker/Associate and Client recipients use their
  existing SignWell routing order.
- Broker oversight / visibility: the selected broker/associate receives the
  completed agreement through the existing SignWell workflow.

## Rendered signed-PDF QA

- Completed packet evidence link or secure reference: private completed
  SignWell packet `5e7765a4`, reviewed September 12, 2026.
- Reviewer: HomeOfferFlow product owner.
- Authenticated QA: the finding was made from the authenticated completed
  SignWell packet, not from a synthetic or unauthenticated public preview.
- Every applicable blank, checkbox, initial, signature, and date visually
  reviewed: the completed signature visual QA found the visible signature and
  date artwork on the printed-name row despite source-rule widget coordinates.
  The source overlay confirms compact intermediary and signer-role X marks are
  inside their printed boxes.
- Locked coordinates / known exceptions: the completed renderer places artwork
  approximately 46 SignWell units above its requested rectangle.  The updated
  execution fields use that measured offset: first row y=734/740 and second
  Client row y=844/850.  A fresh completed packet is still required to confirm
  this corrected production mapping; the prior completed PDF is retained as
  the defect evidence only.

## Regression

- Dedicated golden scenario added: TXR-1507 completed-artwork offset geometry
  is locked in the renderer, SignWell-geometry JSON fixture, and shared text
  baseline.
- Existing buyer-offer regression scenarios run: full local test discovery,
  TXR-1507 renderer tests, signer geometry, SignWell geometry baseline, and
  technical SEO tests.
- Test result / evidence: local test discovery passed after the baseline was
  updated.

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer):
  standing production authorization for HomeOfferFlow corrective releases.
- Approval date: September 12, 2026.
- Approved public-facing scope copy: corrected signature and date placement on
  the Short Form.
- Customer/brokerage source-owner attestation, if this source is private to
  that organization: existing authorized agent attestation applies.

## Deployment decision

- Ready for production: yes, as a bundled corrective release.
- Rollback path: restore the prior TXR-1507 signer-map baseline and deploy the
  preceding production build.
- Post-deploy verification owner: HomeOfferFlow product owner; complete one
  fresh controlled TXR-1507 packet and visually confirm every X, initial,
  signature, and date.
