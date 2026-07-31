# HomeOfferFlow packet/form release evidence

## Release

- Release name: Brokerage identity, TXR authorization gate, and private TXR-1507 renderer QA
- Git commit / pull request: PR #45, branch `release/brokerage-txr-gate-prod`
- Production scope: Brokerage identity/signing metadata plus gated standalone
  TXR workflow foundation. TXR-1507 coordinate corrections were validated only
  against the privately supplied source preview and are not activated for
  production use by this release.

## Approved source

- Approved source form/template and version: TXR-1507 Residential Buyer/Tenant
  Representation Agreement - Short Form, 06-15-26, privately supplied by the
  authorized product owner for QA only.
- Source owner: HomeOfferFlow product owner / authorized source provider.
- Storage location (private only): local private source PDF; not checked into
  the repository or uploaded to shared storage.

## Authorization

- Authority to use this source: Product owner authorized the private source
  PDF for implementation QA. Brokerage-wide and agent-level attestations remain
  required before any restricted TXR form can be used.
- Authorized reviewer: HomeOfferFlow product release review.
- Date confirmed: 2026-07-31.

## Signing plan

- Each recipient and role: Unchanged. Existing buyer, seller, landlord, and
  tenant roles remain governed by the existing packet path.
- Signing order: Unchanged.
- Broker oversight / visibility: Unchanged. Brokerage identity is informational
  in the signing message and does not change recipient access.

## Rendered signed-PDF QA

- Completed packet evidence link or secure reference: Private unsigned TXR-1507
  source preview only; no completed signed-PDF evidence exists yet.
- Reviewer: HomeOfferFlow product release review.
- Every applicable blank, checkbox, initial, signature, and date visually
  reviewed: Source preview reviewed for the corrected purchase percentage and
  intermediary checkbox; completed signing QA is still required before release.
- Locked coordinates / known exceptions: TXR-1507 purchase percentage and
  intermediary coordinates corrected; signature/date widgets remain separate
  and require signed-PDF QA. Existing 20-19 locked coordinates remain unchanged.

## Regression

- Dedicated golden scenario added: Brokerage-branding propagation contract test.
- Existing buyer-offer regression scenarios run: Full automated suite, 275
  tests passed.
- Test result / evidence: `tests/test_txr_1507_renderer.py`,
  `tests/test_brokerage_branding_propagation.py`,
  `tests/test_brokerage_branding_tracker_reconciliation.py`,
  `tests/test_ai_calibration_tracker_reconciliation.py`, and
  `tests/test_brokerage_ops_tracker_reconciliation.py` passed.

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer):
  Andrew Christian / HomeOfferFlow product release review.
- Approval date: 2026-07-31.
- Approved public-facing scope copy: Brokerage identity may appear in the
  signing message; HomeOfferFlow remains a form-completion tool and does not
  provide legal advice or alter the legal form.
- Customer/brokerage source-owner attestation, if this source is private to that
  organization: N/A — no private legal-form source was changed.

## Deployment decision

- Ready for production: no — gated pending PR review, intentional Vercel
  release gate, and completed signed-PDF QA for any activated TXR form.
- Rollback path: Roll back the production alias to the prior Ready deployment;
  no database rollback is required for this communication-only change.
- Post-deploy verification owner: HomeOfferFlow product release review.
