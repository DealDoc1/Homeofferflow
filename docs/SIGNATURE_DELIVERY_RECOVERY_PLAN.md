# Durable signature delivery — implementation in progress

## Required outcome

An owner can recover a failed signature send without rebuilding the interview,
losing the provider document ID, or creating another recipient-facing packet.
Unknown delivery must never be described as definitely sent or definitely
not emailed. Preserve simultaneous invitations, confirmed contacts, source
revision validation, and exact signer geometry.

## Current evidence

The standalone and seller-disclosure routes create a private provider draft,
inspect its fields, then POST /send. They persist its ID only after that final
request succeeds. A send failure/timeout can therefore leave an untracked
provider document. The standalone transient-error cleanup can also delete a
draft without first resolving an ambiguous send outcome. The existing _patch
helper returns no affected-row confirmation and is insufficient for a claim.

Manual status accuracy is corrected in PR #1230; automatic webhook lifecycle
accuracy is corrected in the accompanying webhook change. Those are necessary
prerequisites, not completion of the delivery-recovery work below.

## Next implementation

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

Verify the conditional-write contract in an isolated database before calling
it database-verified. No docker, psql, or supabase executable was found in PATH
on September 15; use an existing approved isolated test environment or install
appropriate local tooling if needed. Do not run race tests against customers.

Retain a truthful release-evidence boundary: local tests, database verification,
GitHub CI, deployment, and production verification are separate. No Vercel
deployment, real recipient send, cancellation, or paid-service change is
authorized merely by adding this implementation plan.
