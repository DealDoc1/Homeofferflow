# Subscribed packet authorization hardening — 2026-08-11

## Release

- Release name: Subscribed packet authorization hardening
- Git commit / pull request: pending release branch
- Production scope: `api/fill-pdf.py` production offer contract packet service authorization only. No PDF source, field mapping, recipient order, or signing payload was changed.
- Changed packet/form target marker: production offer contract packet service.

## Approved source

- Approved source form/template and version: unchanged production 20-19 purchase-offer packet and currently supported addenda.
- Source owner: unchanged.
- Storage location (private only): unchanged; this release neither reads nor writes source files.

## Authorization

- Authority to use this source: unchanged; this release adds server authorization before a packet can be generated.
- Authorized reviewer: HomeOfferFlow product owner standing release authorization.
- Date confirmed: 2026-08-11.

## Signing plan

- Each recipient and role: unchanged from the verified production signing plan.
- Signing order: unchanged.
- Broker oversight / visibility: unchanged; only a verified active, trialing, or free-admin subscription can initiate subscribed packet generation.

## Rendered signed-PDF QA

- Completed packet evidence link or secure reference: no rendering or signing-field change in this authorization-only release; existing production packet evidence remains applicable.
- Reviewer: automated regression plus release reviewer.
- Every applicable blank, checkbox, initial, signature, and date visually reviewed: unchanged because no source PDF, field coordinate, recipient, or signing payload changed.
- Locked coordinates / known exceptions: unchanged.

## Regression

- Dedicated golden scenario added: subscribed packet generation rejects unsigned checkout-shaped requests and requires verified subscription authorization.
- Existing buyer-offer regression scenarios run: full suite.
- Test result / evidence: 785 tests passed locally on 2026-08-11, including the new packet-generation security tests.

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer): standing user authorization for implementation, merge, and production deployment.
- Approval date: 2026-08-11.
- Approved public-facing scope copy: active subscribers can generate packets; unsigned requests cannot.
- Customer/brokerage source-owner attestation, if this source is private to that organization: not applicable; no source asset changed.

## Deployment decision

- Ready for production: yes.
- Rollback path: Vercel rollback to the immediately previous production deployment.
- Post-deploy verification owner: HomeOfferFlow release workflow.
