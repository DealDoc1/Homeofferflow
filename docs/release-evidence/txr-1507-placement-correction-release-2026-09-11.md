# TXR-1507 placement-correction release — September 11, 2026

## Release

- Release name: TXR-1507 Short Form selection and execution placement correction
- Git commit / pull request: `55db5ff` and the preceding TXR-1507 correction commits on `main`
- Production scope: corrective form geometry for `TXR-1507 Residential Buyer/Tenant Representation Agreement — Short Form`, `TXR-1501 Residential Buyer/Tenant Representation Agreement`, `TXR-1506 Buyer's Walk-Through and Inspection`, and `TXR-1508 Buyer/Tenant Representation Agreement`. No source edition, compensation term, recipient plan, or customer interview is changed.
- Changed packet/form target markers: `TXR-1507`, `TXR-1501`, `TXR-1506`, and `TXR-1508`.

## Approved source

- Approved source form/template and version: private TXR-1507, TXR-1501, TXR-1506, and TXR-1508 sources in their approved source-vault revisions; TXR-1507 is revision `06-15-26`.
- Source owner: OnDemand Realty / HomeOfferFlow authorized administrator.
- Storage location (private only): approved private source vault; the source PDF is not committed to this repository.

## Authorization

- Authority to use this source: existing authorized agent attestation and form-use attestation for the approved private source.
- Authorized reviewer: HomeOfferFlow product owner.
- Date confirmed: September 11, 2026.

## Signing plan

- Each recipient and role: the source-specific Client, Buyer, Broker, Associate, and acknowledgement recipients required by each form; TXR-1507 is one or two Clients plus the selected Broker or Broker's Associate.
- Signing order: recipients complete their assigned SignWell fields; no signer receives another party's field.
- Broker oversight / visibility: the selected Broker/Associate box is rendered on the source and the signer receives only the matching shared execution row.

## Rendered signed-PDF QA

- Completed packet evidence link or secure reference: controlled completed packet `d6c614ce` for TXR-1507, stored in the authorized QA download location; the private QA records for TXR-1501, TXR-1506, and TXR-1508 remain the supporting source-specific references.
- Reviewer: HomeOfferFlow product owner and automated source-coordinate regression.
- Completed signature visual QA finding: the existing completed packet showed an intermediary mark outside its printed square and an unmarked Broker/Associate selection box despite execution. It is failure evidence for the old production map, not a certification of that old packet.
- Corrected scope: TXR-1507 source X marks are constrained to their actual printed cells and its Client/Broker/Associate widgets use the measured execution rules; TXR-1501 retainer and role checkboxes, TXR-1506 provider-signature placement, and TXR-1508 acknowledgement marks retain their corresponding source-cell corrections.
- Locked coordinates / known exceptions: a fresh authenticated QA packet is required after this release to visually confirm SignWell's final rendered signature treatment. The already completed packet cannot be retroactively corrected.

## Regression

- Dedicated golden scenario added: TXR-1507 small-cell X bounds and source-specific signer geometry tests, alongside the existing TXR-1501, TXR-1506, and TXR-1508 geometry baselines.
- Existing buyer-offer regression scenarios run: TXR-1501/TXR-1506/TXR-1507/TXR-1508 renderer and signer geometry checks plus production-release and deployment-capacity checks.
- Test result / evidence: 28 focused form/release tests passed locally on September 11, 2026; the production workflow will rerun the complete suite on the exact production artifact.

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer): standing authorization to deploy roadmap fixes and the explicit request to correct this live short-form defect.
- Approval date: September 11, 2026.
- Approved public-facing scope copy: no public copy changes; corrected forms show only the source's normal marks and signing fields.
- Customer/brokerage source-owner attestation, if this source is private to that organization: authorized agent attestation is recorded with the private source workflow.

## Deployment decision

- Ready for production: yes, as a single intentional corrective release.
- Rollback path: restore the immediately preceding verified Vercel production deployment if the canonical health check fails.
- Post-deploy verification owner: HomeOfferFlow product owner; send and complete a new controlled TXR-1507 packet, then inspect every X, initial, signature, and date in the completed PDF.

## Production result

- Deployed commit: `fbf067a757060150d722283da528598b63dd48d3`.
- Production artifact: `https://homeofferflow-ibbd834k5-dealdoc1s-projects.vercel.app`.
- Release workflow: `34560418842`.
- Verification: 1,692 full regression tests passed. The Vercel capacity threshold, prebuilt deployment readiness, canonical-domain response, PWA shell, and packet runtime checks all passed.
- Remaining proof: create and complete a fresh controlled TXR-1507 packet against this release. The previously completed PDF is retained only as the pre-correction visual finding.
