# Automatic draft restoration yields to current work

## Confirmed issue and implementation

Both the delayed page-load handler and account initialization called the same
unconditional local restore function. A late callback could replace an offer
already opened from the workspace, or overwrite newer field edits with the
last local snapshot. Two startup callbacks could also restore the same draft
twice.

Those two callers now explicitly request automatic restore. A page-local
settled flag stops subsequent automatic attempts after a valid restore begins
or the user starts a fresh offer, requests a cloud offer, opens the interview,
or edits an interview field. A payment return also suppresses automatic
restoration. No persistent flag is stored, so normal reload restoration is
still possible.

Manual Resume does not use this automatic restriction. Missing, malformed,
or owner-ineligible drafts do not consume the opportunity to restore later;
an account-owned draft can still restore after its matching session resolves.
Input or change events outside the offer interview do not cancel restoration.

## Verification

- The offer-restore runtime harness has 81 passing cases, including 15 new
  timing and control cases. Against pre-fix `4ccd9f9a`, nine cases reproduce
  unwanted restore behavior; 72 existing/positive controls pass.
- Tests execute actual restore logic and the actual page-load and account-init
  callbacks, with synthetic local storage and a mocked Supabase client.
- Cover current field/state identity preservation, fresh start, pending cloud
  open, interview open, input/change, duplicate automatic restore, payment
  return, manual Resume, outside-form input, missing/malformed drafts, and
  account readiness with and without intervening user action.
- All 45 executable inline scripts parse. `git diff --check` passes.
- Full local suite: **2,000 tests pass in 16.955 seconds**.

These are local runtime tests, not browser visual or live account QA. They do
not prove all startup routes end-to-end or any completed production transaction.

## Account review and release status

The Supabase skill review kept this change at the local restore boundary.
Session acquisition, ownership matching, auth events, API calls, database
queries, and authorization remain unchanged; no live database mutation or
sign-in email was needed. Account-init tests use an in-memory fake provider,
not a claim of production Supabase verification.

Local only. No push, Vercel build, preview, deployment, or added paid service.
Queue with the next authorized cost-controlled release and report as locally
verified until production checks are complete.
