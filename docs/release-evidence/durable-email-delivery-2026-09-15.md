# Durable checkout email delivery — in progress

## Confirmed gap

`api/fill-pdf.py:handle_checkout` calls `send_email` and then the internal
order alert on every invocation. Neither Resend POST has an idempotency key or
a durable email receipt. The signature retry path already avoids repeating
checkout email, but a repeated checkout callback can still repeat these
notifications. This is source-confirmed risk, not proof that a particular
customer received duplicate emails.

Resend retains idempotency keys for 24 hours and requires the same request
body when a key is reused:
https://resend.com/docs/dashboard/emails/idempotency-keys

## Implemented locally, not activated

- `lib/email_delivery.py` implements reserve → stamp first attempt → send with
  one immutable key/body → save provider acceptance.
- `lib/email_delivery_store.py` implements service-only, conditional Supabase
  REST writes. Competing inserts use ignore-duplicates, not merge; a retry
  reads the first saved PDF/body instead of replacing it.
- A confirmed provider receipt suppresses future sends beyond the provider's
  24-hour window. Unknown attempts stop retrying after a conservative 23-hour
  window, pending reconciliation of the original request. The timer is never
  renewed on retry. No claim of exactly-once inbox delivery is made.
- Accepted receipts clear the temporary payload/attachment while retaining a
  compact delivery key, fingerprint, and provider ID. No keys, customer data,
  or signed PDFs are included in test fixtures.
- The protocol distinguishes provider acceptance from recipient delivery.

## Verification and boundaries

24 targeted offline tests pass: provider timeout after acceptance, final-write
failure, late replay, concurrent callbacks, changed PDF/recipient/template,
invalid timestamps, failed persistence, conflicting inserts, and zero-row
conditional updates. The database adapter tests use controlled HTTP responses,
not a live PostgREST table. The full local regression suite passes: **1,884
tests**, including the 24 new delivery tests. `git diff --check` also passes.

Production schema inspection found no existing public email/outbox table to
reuse. No production schema, customer record, email, or deployment was changed.
The code is deliberately not imported by checkout until its storage contract
and integration are complete. Existing production duplicate-email risk remains.

## Remaining implementation

1. Create and verify the private `hof_email_deliveries` schema through the
   normal migration workflow. Required columns: delivery_key (primary key),
   payload (JSON object while pending; null after acceptance),
   payload_fingerprint (SHA-256), status (pending/accepted), first_attempt_at
   (immutable nullable epoch seconds), and provider_id (required when accepted).
   Enforce immutable key/fingerprint/first payload and monotonic state in the
   database, not only application code. Allow payload removal only on accepted
   receipts. Enable RLS; revoke all public/anon/authenticated access; grant the
   necessary table operations only to the backend service role. Do not expose
   a privileged public RPC. Verify constraints, grants, RLS and actual
   conditional-write responses; run advisors before release.
2. Wire buyer packet and admin alert payloads through the same coordinator,
   with separate purpose keys derived only from verified checkout session or
   owned offer identity. Use the actual Resend Idempotency-Key header. Do not
   let browser data choose an arbitrary delivery key. Do not fall back to an
   untracked send when persistence fails.
3. Exercise real checkout route replays and partial failures with controlled
   database/provider responses. Ensure an accepted buyer email is not repeated
   when the admin notification fails. Preserve SignWell identity and packet
   entitlement behavior. Keep showing-booking and other product paths in view;
   do not claim them covered by this buyer-packet work.
4. Provide truthful fulfillment/status responses and a private reconciliation
   path for an old uncertain receipt. Do not auto-resend after the safe window
   or mistake acceptance for inbox delivery.
5. Release with the existing verified batch only when publishing authority and
   deployment cost constraints permit. Verify production separately afterward.

The Supabase security skill informed service-only access, small conditional
writes, and keeping network calls outside database transactions. No new paid
service, worker, polling loop, or Vercel build is introduced.
