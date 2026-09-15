# Signature webhook progress accuracy — September 15, 2026

## Why this accompanies the delivery-recovery work

The manual status refresh was corrected in PR #1230. The webhook path still
treated document_created as sent and document_signed (one signer) as complete.
Those transitions could overwrite the corrected UI or a future durable draft
checkpoint. This change fixes that separate automatic-notification path.

## Implemented

- Exact supported lifecycle-event mapping; unknown events never guess success.
- document_signed and document_in_progress stay partially signed, regardless
  of whether an attached recipient snapshot contains one signer or appears full.
- Only document_completed promotes the packet to signed.
- document_created records aggregate telemetry but performs no packet-status
  update. Creation does not establish an invitation was sent.
- Conditional updates preserve signed/void terminal states, their completion
  timestamps on replay, partial progress on delayed viewed/sent events, and
  viewed status on delayed sent events. NULL detailed status remains eligible
  for the first genuine send/view update.
- Signer-count telemetry no longer interprets unsigned/not-completed text or
  string values such as "false" as a signed recipient.
- Document IDs are URL-encoded in update filters. Existing webhook HMAC
  verification, private-data redaction, and separate packet tables remain.

No new service, dependency, schema value, migration, or recurring polling.
Creation events avoid three unnecessary lifecycle update requests.

## Verification

**1,784 local tests passed.** Nine new tests exercise real verified HTTP webhook
handling, actual event mapping and update construction through a stateful
offline HTTP adapter. Cases include per-signer progress, completion/replay,
late events, void preservation, unknown events, invalid signatures, and
aggregate-count accuracy. Existing standalone, seller-disclosure and webhook
privacy tests remain green. Patch whitespace check passed.

The adapter models PostgREST filter semantics; this is not a newly executed
live Supabase/PostgREST test or production verification. No customer document,
email, signature request, or production data was changed.

Provider event semantics were checked against the
[SignWell events reference](https://developers.signwell.com/reference/events)
and [document status guide](https://help.signwell.com/article/297-types-of-document-statuses).
Conditional update syntax follows
[PostgREST filtering and updates](https://docs.postgrest.org/en/stable/references/api/tables_views.html).

## Remaining work and release boundary

Durable provider-ID storage and same-document retry integration are still in
progress. Their implementation requirements are tracked in
`docs/SIGNATURE_DELIVERY_RECOVERY_PLAN.md`. This prerequisite does not claim
those send-route failures are repaired.

Stacked on PR #1230. GitHub checks only; no Vercel build or deployment requested
while the user's no-overage boundary remains unresolved.
