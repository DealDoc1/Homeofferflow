# Concurrent signing: interview consistency

## Implemented locally

The co-buyer help and seller temporary-lease interview still described sequential
signing after the provider requests were changed to concurrent invitations.
Both instructions now explain that recipients receive signing links together.
The temporary-lease instructions retain the buyer/landlord and seller/tenant
roles without imposing an invitation sequence.

No recipient identity, signature placement, source PDF, contract term, payment,
database record, or already-sent packet was changed. No new service or paid
resource was added.

## Verification

- Full local suite: **1,860 tests pass**.
- Three new interview-copy tests cover the two instructions and reject the old
  sequential wording.
- Two new coordinator tests cover a multi-recipient billing-rejection retry and
  a changed signing-order setting on a saved request. The retry retains both
  recipients and concurrent invitations, creates only one provider document,
  and does not send again after delivery is confirmed.
- Existing agreement/disclosure route tests now require the literal boolean
  `false` at creation and every send attempt, including retry.
- Inspected the actual section markup and stylesheet in isolated headless
  Chrome at 390px and 1100px widths. Both sections were readable, with no
  horizontal overflow. All page network requests were blocked, scripts were
  disabled, and the QA browser was closed afterward. These are isolated layout
  checks, not authenticated full-interview or inbox-delivery verification.
- Provider behavior was checked against the official update-and-send API:
  https://developers.signwell.com/reference/senddocument

## Release state and next step

This batch is local and not deployed. It must ship with the concurrent-delivery
implementation, not ahead of it. Production verification and confirmation of a
fresh simultaneous invitation remain outstanding. Existing sent documents are
not canceled, recreated, or resent as part of this change.

No Vercel build, preview, or deployment was requested. Preserve the cost hold.
The existing daily 08:00 report automation was confirmed ACTIVE; include this
batch as locally verified, not deployed. Public publishing was not retried.
