# Server-owned packet allowance — local release evidence

## Status

Implemented and verified locally; not pushed, migrated, or deployed. Vercel
builds/previews remain on hold for the owner's spending boundary. The separate
public-publishing authorization hold has not been bypassed. No live customer
packet, subscription, usage event, email, or signing invitation was changed.

## Customer behavior

- Subscription generation and authenticated direct PDF downloads share the
  same server-owned packet reservation. Unauthenticated requests cannot enter
  the allowance workflow.
- One unchanged reviewed packet consumes one unit, not one unit per retry.
  Completed retries work at the monthly limit. Changed customer answers or
  uploaded document contents have a different identity. A renderer/source fix
  alone does not charge again for unchanged customer answers; the existing
  signing layer still verifies source revisions and document geometry.
- A definite rendering failure releases its reservation. A timeout after
  completion does not refund possibly completed work or send before the saved
  result is confirmed. Recovery reuses the same reservation/receipt.
- Existing tracked signing packets cannot be silently revised or charged again.
  Historical unkeyed usage is not guessed into a new receipt or recharged: the
  agent is directed to the existing offer's documents/signing status. This is
  not an automatic historical reconciliation or refund.
- The old browser usage-write action returns 410 without mutating usage.
  Browser generation no longer overwrites saved packet status or its signing
  journal after a response or network error.
- Account usage distinguishes completed packets from packets in progress,
  preserves an explicit zero allowance, and uses a server-selected UTC month.
  Pending-work actions open My Offers; allowance actions open Account, not a
  new payment or subscription checkout.
- Paid checkout fulfillment and paid showing notifications remain separate
  from subscription allowance. Subscription requests cannot impersonate paid
  showing checkouts.

## Database contract

Migration `20260915193756_server_owned_packet_usage.sql` adds the private
reservation table, a unique usage-event generation key, and four service-only
RPCs (claim, complete, release, current summary). It was created using the
installed Supabase CLI's migration command, not manually named.

The subscription row is the common lock for short allowance transactions;
rendering and provider calls occur outside those transactions. Attempt tokens
fence stale workers. Lease expiry allows same-packet recovery but never frees
an uncertain reservation into a new quota slot. The read-only summary uses one
database snapshot so completion is not counted as both reserved and used.

RLS is enabled on the new table. Client roles cannot read/write it or execute
the RPCs. Functions are security-invoker with a fixed search path, following
the [Supabase database-function guidance](https://supabase.com/docs/guides/database/functions).
Existing usage rows are preserved; no destructive cleanup/backfill is included.

## Verification

- Full local Python/Node-backed regression suite: **1,959 tests pass**.
- Actual migration SQL executed in fresh isolated PGlite/PostgreSQL:
  **55 checks pass**, including ownership, client-role denial, explicit zero,
  exhausted quota, held slots, duplicate completion, expired-worker fencing,
  month preservation, historical usage protection, and summary accounting.
- API/provider/database doubles exercise the real generation handler,
  service-role RPC adapter, offer saving, and existing signing/email delivery
  layers. Coverage includes a lost database completion response followed by a
  no-charge recovery, direct downloads, authentication, quota denial before
  rendering, and unchanged simultaneous-signing behavior.
- Actual recovery JavaScript verifies that pending work opens saved offers
  and allowance issues open Account without purchasing or generating again.
- Isolated headless Chrome at 390px and 1100px: inspected the actual stylesheet,
  usage card, and recovery notice; no horizontal overflow or script errors.
  Verified the pending-work action and explicit `0 / 0` allowance. External
  page requests were blocked and the browser was closed afterward. This is
  not authenticated end-to-end production QA.

## Remaining release verification

PGlite uses one embedded database session. A subsequent real PostgreSQL 17.10
run verified multi-connection contention; see
`packet-usage-real-concurrency-2026-09-15.md`. Full Supabase/PostgREST integration
and production-schema compatibility still require release-environment checks.
`supabase db advisors --local --type security --level warn --fail-on error`
could not connect to localhost port 54322; an advisor pass is not claimed.

Ship the migration and application changes as one coordinated release, after
checking existing in-flight generation/usage writers. Never deploy the new
application without its RPCs. Verify a full authenticated generation, exact
retry, concurrent request, quota rejection, and delivery-status read against
the release environment. Preserve the ledger on rollback; do not revert to an
older browser-driven usage writer after keyed events have been recorded.

The existing daily 08:00 America/Chicago report automation was confirmed ACTIVE.
Report this batch as locally verified, not deployed or live inbox-verified.
