# Resend delivery-event reporting

HomeOfferFlow can receive delivery events at `/api/resend-webhook`. The route
records only the provider delivery id, event type, provider email id, timestamp,
and allowlisted product tags. It never stores recipients, subjects, property
details, or email content.

## Production setup

After the release containing the endpoint and its Supabase migration is live:

1. In Resend, create a webhook for `https://www.homeofferflow.com/api/resend-webhook`.
2. Select `email.sent`, `email.delivered`, `email.bounced`,
   `email.complained`, `email.suppressed`, `email.opened`, and `email.clicked`.
3. Set the generated signing secret as the encrypted Vercel production
   environment variable `RESEND_WEBHOOK_SECRET`.
4. Send a controlled test email and use Resend's replay control if needed.
5. Confirm exactly one row is recorded for the event's `svix-id` and that the
   saved `tags` contain only `email_type`, `seller_package`, or `partner_tier`.

The handler verifies the raw request body using Resend's Svix headers, rejects
stale or invalid signatures, and makes duplicate webhook deliveries harmless.
Resend manages its own suppression behavior; this ledger gives HomeOfferFlow
the delivery evidence needed for operational follow-up and aggregate reporting.
