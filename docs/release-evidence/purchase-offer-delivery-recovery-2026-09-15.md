# Purchase-offer signature recovery — September 15, 2026

## Implemented; not deployed

Purchase offers now use the same private-draft, durable-checkpoint, verified-send
coordinator as standalone agreements and seller disclosures. The authenticated
owner's offer ID or a server-verified checkout ID determines the saved record.
The record and SignWell ID are confirmed saved before invitations are requested.

Retries inspect and reuse the same provider document. A rejected send can resume
without sending another PDF, charging again, or consuming another entitlement.
An uncertain send retains its tracking journal and status-check instructions.
Already sent or completed requests reconcile without another invitation. A failed
database claim cannot send its private draft; initial creation races can leave an
unused private draft, so this does not promise zero private orphan documents.

All named recipients retain simultaneous invitations and existing field
assignments. No live customer packet was sent, replaced, canceled, or modified.

## Identity and status protection

- Owner, record, document ID, state, and last_updated constrain send claims.
- Each renderer call records hashes of the exact template bytes it reads;
  uploaded Paragraph 4 sources are separately hashed. Variable PDF timestamps
  are not treated as content changes. Request-local collectors reset on failure.
- Provider verification rejects changed recipient names/emails, moved fields,
  duplicate or unidentified field IDs, and non-finite geometry.
- Offer refresh uses version checks and confirms exactly one updated row.
  Completed states cannot regress; Submitted, Accepted, and Deleted business
  states are retained when signature details refresh.
- Declined/canceled provider states map to the existing Rejected database value.
  The live and isolated QA table constraints were read to verify allowed values.
- The retry UI does not call successful delivery a failure if the list fails to
  reload. Completed recovery explicitly says no new invitation was sent.

## Verification

- **1,848 local tests passed** in 11.379 seconds, 32 more than parent PR #1232.
- Thirteen purchase integration cases execute the actual checkout/retry handler,
  adapter, and coordinator with offline HTTP doubles. Coverage includes rejected
  sends, sent/draft timeout outcomes, guest and owned checkout replay, changed
  source/email, save failure, zero-row claim, final-write recovery, ownership,
  and legacy tracked-document refusal. Provider create/send counts are asserted.
- Node executes the shipped offer retry handler: authentication, successful send
  with failed list refresh, uncertain delivery, and already-completed recovery.
  These are handler tests, not a rendered-browser end-to-end session.
- **Six rollback-only SQL assertions passed** on the existing isolated
  stripe-lifecycle-qa branch for initial/resume claims, stale versions,
  wrong-owner rejection, and terminal-state protection. A follow-up query found
  **zero remaining fixture rows**. No schema changes or production data writes.
- **All 12 golden packet rendering scenarios match the approved baseline**.
  This checks rendered layout, not a newly completed SignWell signature PDF.
- git diff --check passed. GitHub CI result will be recorded in the PR.

## Release and cost boundary

This is stacked on PR #1232 (21b65e3e). Vercel Git deployments remain disabled;
no preview, build, production dispatch, paid service change, or new QA branch
is requested. The no-overage deployment hold remains in effect. Daily reporting
is still ACTIVE at 08:00 America/Chicago.

Not claimed: live inbox receipt, production execution of the new sender,
multi-session database concurrency QA, or fixes to previously reported signed
PDF placement. Checkout event replay can still repeat the ordinary attached-PDF
email; this batch prevents duplicate signature invitations, not every email.
