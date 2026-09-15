# Saved signature-request recovery — September 15, 2026

## Implemented locally

Standalone TXR agreements and reviewed seller disclosures now create a private
SignWell draft, save its ID and request fingerprint, inspect its fields and
recipients, claim the send attempt, then send that same document. The fingerprint
includes account/record identity, source revision and source bytes, structured
answers, signing geometry, recipient identities, and relevant rendering profile
information. Non-deterministic PDF timestamps are excluded.

All recipients still receive simultaneous invitations. No signature geometry,
legal wording, source authorization, or named signer assignment is changed.

Rejected sends remain recoverable using the saved document. An uncertain send
is inspected once and is never described as definitely unsent. A saved draft
has a two-minute retry cooldown after an ambiguous send. Already sent/completed/
void provider states reconcile without another invitation. No recovery path
deletes, cancels, or replaces the tracked provider document. Concurrent initial
creation may leave an unused private draft if its claim loses; it cannot send.

Database claims include owner, record, expected document ID, draft/failed state,
and expected updated_at. Exactly one returned row is required. Final writes
preserve newer signed/void state. Manual agreement/disclosure refreshes now
also use version checks, preventing stale JSON from overwriting the retry journal
or a newer completion. A stale refresh reports that another update occurred.

## User experience

- Retry saved request appears for eligible tracked drafts, with saved contacts.
- Legacy tracked documents without a recovery journal offer status refresh;
  they are never blindly duplicated.
- A successful send is not reported as failed if the subsequent list refresh
  fails. Completed-request recovery explicitly says no new invitation was sent.
- Internal attempt metadata is not displayed as seller-disclosure answers.

## Verification

Full local regression: **1,816 tests passed** (11.177 seconds). This is 32
additional tests relative to the parent release stack. git diff --check passed.

The tests execute the coordinator, real route functions and HTTP adapter using
offline provider/database doubles. Cases cover zero-row claims, concurrent
clicks, unchanged-ID retry after 402 rejection, timeout with draft/sent/completed
results, fingerprint and geometry mismatch, cooldown, final-write failure, and
completion arriving before final persistence. No real invitation was sent.

Node executes the shipped UI submit handler and retry controls, including a
successful send followed by a failed list refresh and already-completed recovery.
This is event-handler verification, not rendered-browser or physical-device QA.

The existing isolated Supabase QA branch passed six rollback-only SQL assertions
on the standalone table. These establish conditional update behavior, stale
version rejection, owner filtering, and terminal-state preservation. A separate
query confirmed zero fixture rows remained. No schema migration, production
record change, or new paid branch was created. This is not production RLS or
multi-session database concurrency verification.

## Release boundary and unfinished scope

Local changes only until the associated PR/CI evidence is recorded. No Vercel
build, preview, or deployment is triggered: Git deployment is disabled and no
production-release workflow is dispatched. The user's no-overage boundary stays
in effect. Existing live customer packets are unchanged.

Purchase-offer recovery in api/fill-pdf.py remains in progress. This batch does
not claim that every signing workflow has completed recovery QA, that email
arrived in an inbox, or that prior signature-placement issues are resolved.
