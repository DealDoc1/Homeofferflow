# Intentional production release — current verified main — 2026-08-08

## Scope

This release bundles the verified current `main` state into the existing
HomeOfferFlow production deployment. It preserves the current 20-19 purchase
offer flow, supported purchase addenda, seller temporary residential lease,
OnDemand launch copy, field-mapper safeguards, and release/preflight checks.

## Field, checkbox, and signature QA

- Full Python regression suite: 514 tests passed in the pinned test environment.
- Seller Temporary Residential Lease completed packet: 14 rendered pages
  visually inspected; contract fields, Paragraph 22 checkboxes, initials,
  buyer/seller signatures, dates, lease terms, notices, and contact fields were
  seated on their intended lines.
- Golden purchase-packet rendering guard passed for the approved baseline.
- Four restricted TXR source forms (TXR-1501, TXR-1506, TXR-1507, TXR-1508)
  have passed local unsigned render inspection only. They are not activated
  for production send/signing in this release because authenticated point-of-
  use QA and completed-signature visual QA remain outstanding.

## Deployment boundary

- Production offer-generation route remains the current 20-19 implementation.
- No 20-18 production route or PDF was modified.
- No restricted TXR source was newly distributed or enabled.
- Post-deploy canonical smoke and runtime-error comparison remain required.
