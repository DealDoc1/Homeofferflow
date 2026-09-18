# Resend suppression visibility — September 18, 2026

## Outcome

HomeOfferFlow now recognizes Resend's `suppression.added` and
`suppression.removed` webhook events in the existing authenticated, idempotent
delivery-event route. This gives the private admin dashboard early visibility
when Resend adds an address to the team-wide suppression list, before another
customer-facing email is attempted.

This follows Resend's documented team-level suppression lifecycle:
<https://resend.com/changelog/suppression-list-support>.

The dashboard reports only aggregate added/removed counts. A new suppression
increases the existing email-delivery attention count. A removal is recorded
without creating an alert. Neither event is included in the terminal email
delivery-rate denominator because neither represents an attempted email.

## Privacy and cost boundary

The event row stores no recipient address, suppression origin, subject,
message, provider payload, or source contact. The browser still receives only
aggregate counts. Existing Svix signature verification, replay protection, and
server-only database access remain unchanged.

The enhancement uses the webhook HomeOfferFlow already operates. It adds no
polling, scheduled function, analytics service, database table, provider API
request, or paid dependency.

## Verification

Focused webhook and admin-dashboard tests verify:

- both supported suppression lifecycle events are processed;
- an email address present in the provider payload is not persisted;
- unknown event types remain ignored;
- the aggregate-only admin response contract remains intact; and
- customer-facing pages do not expose event rows or recipient identifiers.

Production setup must add `suppression.added` and `suppression.removed` to the
existing Resend webhook subscription when this release is deployed. No Resend,
Supabase, Vercel, or production account setting changed in this local batch.
