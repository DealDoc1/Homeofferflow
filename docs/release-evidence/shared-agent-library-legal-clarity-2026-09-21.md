# Shared agent library legal clarity — 2026-09-21

## User problem

The public Terms and Disclaimer still described a brokerage-authorization and
per-use-attestation gate for some Texas REALTORS® forms. That contradicted the
released product: every form shown in HomeOfferFlow's shared agent library is
available to every signed-in agent without a brokerage seat. The same copy also
exposed the internal phrase `source-gated` to customers.

## Candidate change

- Replace the obsolete brokerage-seat and per-use-attestation language in the
  Terms and Disclaimer with the actual shared-library access model.
- Preserve the user's responsibility to confirm form-use rights, suitability,
  authority, licensing, and lawful use.
- Replace internal release terminology with plain customer-facing language:
  draft only, under review, unavailable, or not yet released.
- Advance the coordinated policy package to Version 3.1 dated September 21,
  2026, and use acceptance version `2026-09-21` in the offer and OnDemand
  flows.

## Verification

- Focused legal, acceptance-record, OnDemand, and subscription-checkout tests:
  40 passed.
- Local browser verification:
  - `/terms.html` returned 200 and exposed the Version 3.1 access language in
    the accessibility tree.
  - `/disclaimer.html` returned 200 and rendered the complete policy page with
    the shared-library statement visible and no layout break.
  - No internal `source-gated` wording remains on either public legal page.
- Full repository suite: 2,385 tests passed in 71.658 seconds.

## Release status

Implemented and locally verified. This change is not production-live until the
single coordinated post-reset Vercel release completes and the canonical legal
pages and acceptance paths are verified.
