# Private checkout packet storage

## Outcome and scope

The buyer checkout sender now saves the exact serialized offer privately before
creating a Stripe session. Stripe receives four metadata values (plan, payment
email, payload ID and SHA-256), not offer answers or uploaded PDF data. The
session is bound to the saved payload before the browser receives its payment
URL. An unconfirmed binding returns no URL and attempts to expire the session.

The signed payment fulfillment path loads only the matching session/payload,
checks the hash, paid or zero-total status, payment mode, plan and receipt
email, then uses the existing rendering/signing/email flow. Authenticated
subscription requests cannot resolve checkout references. Failed reference
checks cannot fall back to attacker-supplied inline answers. Previously created
inline-metadata checkout sessions remain supported.

This supersedes the sender-side chunking described in
`checkout-unicode-preservation-2026-09-15.md`; exact text preservation remains
covered across the Node/Python boundary.

## Security and cost

The payments and Supabase/database skills guided external payload storage,
service-only privileges, RLS, immutable answers and one-time session binding.
No new package, paid service, browser permission, form-availability gate or
signature-order change is introduced. The entire saved JSON is bounded to
4 MiB, enough for the advertised 2.5 MiB attachment content plus base64
encoding and normal offer answers. Oversize requests fail before storage or
Stripe calls. Storage errors are redacted from the public response and logs.

The private table retains payloads for fulfillment retries and reconciliation;
this change does not yet add a retention/cleanup worker. An abandoned-checkout
cleanup policy is follow-up work, not a completed cost optimization. Do not
delete a paid or uncertain packet merely because it is old. Existing failed
or previously sent customer packets are not changed or resent by this work.

Primary references checked September 15:
- https://docs.stripe.com/metadata
- https://supabase.com/docs/guides/database/postgres/row-level-security
- https://supabase.com/changelog (including the Data API grant change)

## Verification

- 12 Node sender/storage cases: full-size attachments, saved-before-checkout
  sequencing, small metadata, exact binding, provider failures/timeouts,
  wrong/empty acknowledgements, missing configuration and oversize rejection.
- The full-size test fails against `56eac84b` specifically because the old
  sender exceeds Stripe's metadata key limit; the changed sender passes.
- Python loader tests cover Unicode, paid/zero-total sessions, invalid IDs,
  wrong plan/email/session, missing/duplicate/corrupt records and redaction.
- Cross-language integration executes the real Node sender and Python
  fulfillment with mocked HTTP providers, preserving 2.5 MiB of synthetic
  attachment bytes plus Unicode at the PDF rendering boundary. It does not
  render those synthetic bytes or constitute PDF visual QA.
- Existing reference-independent checkout, numeric validation, signed relay,
  signing and email retry regression tests remain green.
- Actual migration executed in isolated PGlite/PostgreSQL: 25 checks pass,
  including client read/write denial, RLS even after accidental read grants,
  immutable body/hash, one-time binding and full-size storage round trip.
  This is not hosted Supabase/PostgREST integration verification.
- Full local Python suite: **2,014 tests pass in 17.802 seconds**. The Node
  suites run through Python wrappers. `git diff --check` passes.

## Rollout status and requirements

**Local only; not deployed.** No GitHub push, production database write,
Vercel build, live checkout, customer signature or customer email occurred.

Before release, apply and verify
`20260915233303_private_buyer_checkout_payloads.sql` in the intended database,
confirm the existing server-only Supabase URL/service key are available to
the Node checkout function, then release sender, relay and reader together.
Verify a noncustomer test-mode checkout through the hosted Data API/provider
boundary before claiming end-to-end completion. Existing release cost and
publication restrictions remain in effect.

Rollback must preserve the reference-aware receiver for already-created
reference sessions; reverting to an inline-only receiver would break their
fulfillment. Do not drop the payload table on rollback.

The existing 08:00 America/Chicago daily report automation was confirmed ACTIVE
from its configuration during this work. This does not prove a future run.
