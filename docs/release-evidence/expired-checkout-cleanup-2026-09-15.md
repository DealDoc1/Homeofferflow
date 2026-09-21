# Expired buyer-checkout staging cleanup

## Implemented locally

The existing Stripe webhook now handles `checkout.session.expired` after its
signature verification, live/test isolation and duplicate-event checks. It
removes only a reference-backed self-service payment packet when Stripe reports
both `status=expired` and `payment_status=unpaid`.

The delete matches the exact payload UUID and fingerprint and either the same
Stripe session or an unbound row left by a lost creation/binding acknowledgement.
A packet bound to another session cannot match. Already-removed rows are safe
on retry. A failed/ambiguous storage response marks the event failed and returns
a retryable webhook response rather than silently claiming cleanup succeeded.

Paid/zero-total, open/complete, subscription, partner, seller, legacy inline and
invalid-reference sessions are excluded. Recovery-enabled sessions and sessions
copied from another checkout are retained. Browser cancellation and packet age
are not cleanup authority. No periodic scanner, new service, Vercel cron, Stripe
API polling or customer-facing permission prompt is introduced.

The payments and Supabase security skills guided signed-event authority and
backend-only deletion privileges. The new migration grants DELETE only on the
staging table to `service_role`; clients still have no access and RLS remains
enabled. Other offers, signatures, emails, invoices and source PDFs are untouched.

References checked:
- https://docs.stripe.com/payments/checkout/abandoned-carts
- https://docs.stripe.com/api/checkout/sessions/expire
- https://supabase.com/docs/guides/database/postgres/row-level-security

## Verification

- 14 new Python tests pass: exact scoped requests, safe retries, negative
  product/payment/recovery cases, provider errors, and the real webhook route
  using valid/invalid HMAC signatures. Signed sandbox events cannot reach
  production cleanup, and a test secret cannot authorize a live deletion.
- The isolated PGlite/PostgreSQL schema suite now passes 32 checks, including
  exact-match deletion, wrong hash/session preservation, an unbound expired
  copy, repeat deletion, and absence of client DELETE privileges.
- Full local suite: **2,028 tests pass in 17.759 seconds**.
- `git diff --check` passes.

Only synthetic local database rows were deleted during QA. No production data,
live payment, customer email, signature or provider configuration was changed.

## Deployment and remaining work

**Not deployed.** Apply `20260915234223_expired_checkout_payload_cleanup.sql`
after the private checkout storage migration, release with the reference-aware
sender/receiver, verify that the intended Stripe webhook endpoint subscribes to
`checkout.session.expired`, and verify a test-mode expiration in the isolated
environment. Hosted Supabase/PostgREST and provider event delivery are unverified.

This completes the event-driven portion of abandoned-packet cleanup, not a
general retention policy. Rows from failed session creation without any Stripe
expiration event, recovery-enabled sessions and paid packets remain retained.
Those need reconciliation/retention work based on authoritative payment and
fulfillment evidence; do not add blind age-based deletion. Missing historical
events are not assumed to have been delivered.

This extends `private-checkout-payloads-2026-09-15.md`. The no-push/deployment-cost
restrictions remain in effect; no Vercel build was started.
