# Durable signature delivery — implementation in progress

## Required outcome

An owner can recover a failed signature send without rebuilding the interview,
losing the provider document ID, or creating another recipient-facing packet.
Unknown delivery must never be described as definitely sent or definitely
not emailed. Preserve simultaneous invitations, confirmed contacts, source
revision validation, and exact signer geometry.

## Current evidence (updated September 15)

The local standalone, seller-disclosure, and purchase-offer routes now use lib/signwell_delivery.py:
private creation, owner/version-scoped identity checkpoint, provider inspection,
conditional send claim, same-document send, and non-regressing status save.
The UI exposes Retry saved request only for eligible tracked drafts. Neither
route deletes documents after a send failure. This is not deployed yet.

Manual status accuracy is corrected in PR #1230; automatic webhook lifecycle
accuracy is corrected in the accompanying webhook change. Those are necessary
prerequisites, not completion of the delivery-recovery work below.

## Recovery contract

1. Introduce one tested delivery coordinator for existing document identity,
   request verification, persistence, sending, and recovery. Inspect the
   purchase-offer retry path separately and apply the same identity guarantees
   where its creation/send behavior differs; do not assume the three routes
   currently have the same implementation.
2. Save the provider ID before any recipient-facing send. Use an owner-scoped
   conditional update with return=representation and require exactly one
   matching row. A concurrent request or failed/uncertain save must not proceed
   to sending. Keep the root dirty working tree untouched.
3. Retain an attempt journal in existing structured packet data, not only in
   signwell_status: refreshes and webhooks legitimately change that status.
   Include an attempt identifier/time, phase, document ID, and a request
   fingerprint. Use updated_at or the expected journal version in conditional
   updates. Do not introduce browser-controlled authorization claims.
4. Fingerprint owner/record identity, form/source revision, structured form
   inputs, signing map, and confirmed recipients. Put that fingerprint in
   provider metadata and verify it with the returned field/recipient list on
   retries. Do not fingerprint nondeterministic PDF creation timestamps or
   trust a mutable client journal alone as evidence of document identity.
5. A tracked retry must inspect that same provider document first. Reconcile
   an already sent/completed/void result without another creation or send.
   Resume only a verified private draft with unchanged contents/recipients.
   Reject legacy tracked records lacking sufficient identity evidence with
   a clear refresh/recovery action, never a blind replacement.
6. Serialize resume attempts and apply a bounded cooldown after an ambiguous
   in-flight send. On timeout/non-success, inspect the same ID once. Never
   delete, cancel, replace, or repeat creation for an uncertain result. A
   create-before-save crash may leave an unused private draft; it must never
   have been sent by this workflow. Do not falsely promise zero private orphans.
7. Final writes must not overwrite a webhook's newer signed/void state. A
   persistence failure after a successful send remains recoverable through
   the checkpoint and a read of the same provider ID.
8. Expose a concise same-document retry/status action for supported tracked
   drafts. Keep recipient confirmation and source/field verification. Separate
   a successful send from a failed subsequent list refresh in the UI, so the
   latter cannot be presented as a failed invitation.

## Required verification before claiming recovery complete

Exercise the actual route/coordinator through initial send, concurrent claims,
claim returning zero rows, persistence timeout, inspection failure, altered
fields/recipients/fingerprint, provider rejection, send timeout followed by
draft/sent/completed/unknown state, malformed response, stale attempt, parallel
resume, and final-write failure. Assert provider creation/send counts and
owner/record/document filters. Check known-unsent versus uncertain user copy.

The connected isolated stripe-lifecycle-qa branch was available September 15.
Six rollback-only SQL assertions passed for initial/resume claims, stale
versions, wrong-owner rejection, and preserving signed state. A follow-up
query confirmed zero fixture rows remain. This verifies the conditional SQL
contract, not simultaneous real database sessions or production RLS.

## Remaining work

- Purchase-offer creation and retry now use the shared coordinator through
  lib/offer_signwell_delivery.py. Local checkout/retry integration, UI handler,
  field validation, and source-manifest isolation tests pass. Six additional
  rollback-only offer-table SQL assertions passed; zero fixtures remain.
- Full local suite: 1,848 passing tests. All 12 golden packet rendering
  scenarios match the approved baseline. These are not live inbox or completed
  signature checks, and do not prove simultaneous real database-session behavior.
- Finish release/CI review and production verification when spending permits.
- No new live recipient send, inbox receipt, or signed-PDF visual QA was run
  for this change. Do not mark the overall recovery item complete yet.

Retain a truthful release-evidence boundary: local tests, database verification,
GitHub CI, deployment, and production verification are separate. No Vercel
deployment, real recipient send, cancellation, or paid-service change is
authorized merely by adding this implementation plan.
