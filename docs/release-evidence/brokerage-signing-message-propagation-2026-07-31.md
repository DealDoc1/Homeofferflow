# HomeOfferFlow packet/form release evidence

## Release

- Release name: Brokerage identity in signing messages
- Git commit / pull request: PR #45, branch `release/brokerage-txr-gate-prod`
- Production scope: SignWell request message and metadata only; no PDF bytes,
  source form, field map, recipient role, signature coordinate, or signing order
  changed.

## Approved source

- Approved source form/template and version: N/A — this batch does not add or
  modify a legal-form source.
- Source owner: N/A — no legal-form source was changed.
- Storage location (private only): N/A.

## Authorization

- Authority to use this source: N/A — no legal-form source was changed.
- Authorized reviewer: HomeOfferFlow product release review.
- Date confirmed: 2026-07-31.

## Signing plan

- Each recipient and role: Unchanged. Existing buyer, seller, landlord, and
  tenant roles remain governed by the existing packet path.
- Signing order: Unchanged.
- Broker oversight / visibility: Unchanged. Brokerage identity is informational
  in the signing message and does not change recipient access.

## Rendered signed-PDF QA

- Completed packet evidence link or secure reference: Existing approved golden
  packet and signed-PDF evidence remain unchanged; this batch does not alter
  rendered PDF content.
- Reviewer: HomeOfferFlow product release review.
- Every applicable blank, checkbox, initial, signature, and date visually
  reviewed: Not applicable to this communication-only change; no PDF content or
  coordinates changed. Existing golden rendered-PDF regressions were rerun.
- Locked coordinates / known exceptions: All existing locked coordinates remain
  unchanged.

## Regression

- Dedicated golden scenario added: Brokerage-branding propagation contract test.
- Existing buyer-offer regression scenarios run: Full automated suite, 275
  tests passed.
- Test result / evidence: `tests/test_brokerage_branding_propagation.py`,
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

- Ready for production: yes, pending the ordinary PR review and intentional
  Vercel release gate.
- Rollback path: Roll back the production alias to the prior Ready deployment;
  no database rollback is required for this communication-only change.
- Post-deploy verification owner: HomeOfferFlow product release review.
