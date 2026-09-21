# Packet allowance: real PostgreSQL concurrency verification

## Outcome

The packet-usage migration was executed against isolated PostgreSQL **17.10**
with **eight independent backend connections**, not PGlite or mocked queries.
The expanded run passed **54 checks** across the scenarios below.
The full application regression suite also remains green: **1,959 tests**.
The runner observes real database lock waits before releasing each race.
No production schema, usage balance, customer document, or provider was touched.

The pinned runtime lives outside application dependencies. Tests use a private
Unix socket with TCP disabled and a newly initialized synthetic database. The
cluster is stopped after each run; no background database is left running.

## Scenarios

- Five races for one remaining packet slot: one reservation and seven quota
  rejections in each round.
- Eight completion attempts for each winner: one usage event and one receipt.
- Eight requests for the same packet: one worker admitted and seven busy.
- Expired-request recovery: old completion/release attempts wait, then cannot
  change the replacement worker's reservation.
- Summary reads before/after commit see either one reserved or one used unit,
  never both.
- A locked account does not block another account's reservation.
- A waiting replacement can use a definitely released reservation once.
- Disconnect before commit rolls back the usage event and completion together;
  a subsequent completion can recover the original reservation.
- A queued generation observes a committed inactive billing status.
- Anonymous and authenticated roles cannot invoke private quota RPCs.

Run instructions and package lock are in `scripts/qa/postgres-runtime/`.
`scripts/qa/check_packet_usage_concurrency.cjs` does not accept a production URL.

## Scope remaining

The earlier single-session concurrency limitation is now resolved for the
isolated PostgreSQL schema. Full Supabase/PostgREST integration, full production
schema compatibility, and an authenticated end-to-end release run remain
unverified. The earlier failed local Supabase advisor invocation is not
reclassified as a pass by this test.

No Vercel build, preview, deployment, GitHub push, live email, or signature
request was made. Keep the spending/publishing holds and include this progress
in the existing daily report as **locally verified**, not deployed.
