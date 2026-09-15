# Durable checkout email delivery — in progress

## Confirmed gap

Before this local change, `api/fill-pdf.py:handle_checkout` called `send_email`
and then the internal order alert on every invocation. Neither Resend POST had
an idempotency key or a durable email receipt. The signature retry path already avoids repeating
checkout email, but a repeated checkout callback can still repeat these
notifications. This is source-confirmed risk, not proof that a particular
customer received duplicate emails.

Resend retains idempotency keys for 24 hours and requires the same request
body when a key is reused:
https://resend.com/docs/dashboard/emails/idempotency-keys

## Implemented locally, not activated

### Integration update

The local checkout route now uses the coordinator for buyer PDF and admin
order emails. Purpose keys are separate; paid-order identities come from
verified checkout sessions, and subscription identities bind a verified owner,
saved offer ID, and reviewed answer fingerprint. Identical callbacks reuse
the same request; intentional changes to an owned offer's answers can produce
a distinct document email. No caller-supplied email key is trusted.

The Supabase CLI generated
`20260915185113_durable_checkout_email_delivery.sql`. Its trigger prevents request identity,
pending body, and first-attempt timestamp changes, and prevents confirmed
receipt regression. The backend cannot delete receipt rows. Client roles have
neither table grants nor an RLS policy that exposes rows.

Updated verification: **1,894 Python tests pass**. Ten new checkout tests cover
replay, PDF/template changes after provider timeout, admin failure recovery,
owned-offer revisions, invalid identities, ignored browser email-key hints, and the separate showing path.
Existing full signing-route tests now also exercise the real email store's
HTTP contract and verify buyer/admin emails are not repeated.

An isolated PGlite 0.5.8 PostgreSQL runtime executes the migration with 26 passing checks of
schema constraints, conditional claims, immutable fields, service-only access,
RLS defense in depth, and acceptance cleanup. The CLI 2.117.0 migration tool
and PGlite are temporary QA tools, not production app dependencies. The full
Supabase CLI security advisor was attempted against localhost but could not
connect because the Docker Supabase stack is not running. Targeted PostgreSQL
schema/security checks pass; live PostgREST/grant checks and hosted advisors
remain required before activation. No production table was created.

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

### Verified-webhook recovery update

Latest full regression: **1,909 tests pass** (15 additional recovery/adapter
tests); `git diff --check` passes. The earlier counts below are historical
checkpoints, not the current suite total.

Newly reserved durable emails include two opaque Resend tags: the delivery key
and a digest of the complete original request, including PDF attachment bytes.
The database still fingerprints the entire tagged request, and retries use the
original saved body. An existing untagged reservation is not rewritten.
Resend documents tags in webhook events:
https://resend.com/docs/dashboard/emails/tags

The existing `/api/resend-webhook` route now reconciles matching checkout
receipts only after checking the signature over the untouched request body.
Matching requires the exact saved delivery key, content digest, sender,
recipients, and a valid provider email ID. Corrupt, missing, unattempted,
untagged, and mismatched requests are not accepted. The receipt adapter has
no send capability. A confirmed pending receipt transitions through the same
conditional service-only write and clears its private payload.

Reconciliation runs before claiming event telemetry, including for replayed
events. A database failure returns a retryable webhook error. If the receipt
write succeeds and telemetry subsequently fails, a replay recognizes the same
accepted provider ID without sending or overwriting it. Existing telemetry
continues to omit receipt correlation tags, addresses, subject, and PDF data.

Tests exercise a real signature-verified handler through the coordinator with
controlled storage, a seven-day-old timeout, repeated/out-of-order events,
wrong identities, attachment tampering, and write failure/recovery. Bounces
confirm provider acceptance only; they remain bounces in delivery telemetry.
No live Resend event or inbox receipt was verified in this update.

### Operational recovery after release

1. For a pending tagged request, locate the original email in Resend and replay
   its original provider event to the configured webhook. Replaying an event
   is not resending the email. Use the authenticated Resend dashboard, never a
   browser-supplied claim of delivery or a hand-edited webhook payload.
2. Verify the exact private receipt has changed to `accepted` with the original
   provider ID and cleared payload. Check the separate delivery event for
   delivered, bounced, or suppressed status; acceptance alone is not delivery.
3. Repeating checkout after reconciliation reuses the accepted receipt instead
   of requesting another document email. This path is locally tested only.
4. If there is no matching provider event, the webhook is unsubscribed from
   the relevant event, or the message predates these tags, do not manufacture
   an accepted receipt or reset its retry window. A separate exact-ID provider
   lookup/operator recovery path remains to be built. Legacy messages are not
   claimed recovered by this update.

Production release must verify the existing webhook subscription and replay
one controlled event end to end. No new webhook, subscription, polling task,
database column, or paid service was created by this update.

24 targeted offline tests pass: provider timeout after acceptance, final-write
failure, late replay, concurrent callbacks, changed PDF/recipient/template,
invalid timestamps, failed persistence, conflicting inserts, and zero-row
conditional updates. The database adapter tests use controlled HTTP responses,
not a live PostgREST table. The full local regression suite passes: **1,884
tests**, including the 24 new delivery tests. `git diff --check` also passes.

Production schema inspection found no existing public email/outbox table to
reuse. No production schema, customer record, email, or deployment was changed.
The local checkout integration requires this migration before deployment.
Existing production duplicate-email risk remains until deployment and live
verification; local tests do not establish production or inbox delivery.

## Remaining implementation

1. Apply and verify the locally tested private `hof_email_deliveries` schema through the
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
2. Production-verify the locally wired buyer packet and admin alert payloads through the same coordinator,
   with separate purpose keys derived only from verified checkout session or
   owned offer identity. Use the actual Resend Idempotency-Key header. Do not
   let browser data choose an arbitrary delivery key. Do not fall back to an
   untracked send when persistence fails.
3. Retain the passing real checkout route replay and partial-failure tests with controlled
   database/provider responses. Ensure an accepted buyer email is not repeated
   when the admin notification fails. Preserve SignWell identity and packet
   entitlement behavior. Keep showing-booking and other product paths in view;
   do not claim them covered by this buyer-packet work.
4. Provide truthful fulfillment/status responses and a private reconciliation
   path for an old uncertain receipt. Do not auto-resend after the safe window
   or mistake acceptance for inbox delivery. The route now reports provider
   acceptance explicitly and distinguishes unconfirmed admin email. Admin
   failures remain non-blocking for the buyer; another callback can resume
   that receipt, but no autonomous admin-email retry worker was added. An old
   uncertain tagged receipt can now reconcile through the verified webhook;
   legacy/no-event recovery and live verification remain in progress.
5. Release with the existing verified batch only when publishing authority and
   deployment cost constraints permit. Verify production separately afterward.

The Supabase security skill informed service-only access, small conditional
writes, and keeping network calls outside database transactions. No new paid
service, worker, polling loop, or Vercel build is introduced.
