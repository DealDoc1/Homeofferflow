# Stable packet delivery retries — local verification

## Reproduced defect

The existing purchase-checkout integration test failed after adding only refreshed
`generatedAt` / `packetGeneratedAt` browser values to an otherwise identical offer.
The allowance identity already ignored these fields, but the signing fingerprint
and document-email identity did not. That could reject a valid signing recovery
and create a different email-outbox key for the same packet.

## Fix

For a server-read, authorized, already-tracked packet, compare the current request
with the saved original, disregarding only six explicit UI-bookkeeping fields.
If every other input matches, reuse the original fingerprint inputs, including any
timestamp values originally present. This preserves existing provider fingerprints
and email keys rather than changing the fingerprint algorithm or creating receipts.

Retry checkpoints retain the same original inputs. This matters when another
provider rejection occurs: the following retry must still match the original
document. Customer fields, uploaded attachment contents, source hashes, rendering
revisions, recipients, and signature placement remain significant and subject to
the existing checks. JSON types remain distinct. No broad underscore-field exclusion
was introduced in the signing comparison.

The email integration guidance informed keeping the existing deterministic-key and
immutable-outbox behavior. No new provider requests, schema changes, dependencies,
fallback sends, or changes to signing order were added.

## Evidence

- Regression reproduced against the unmodified sender, then passed after the fix.
- Focused suite: **26 tests passed**. Actual purchase-checkout/signing-retry code
  executed with controlled database/provider doubles; no network sends.
- Timestamp-only replay: one provider document, one signing send, one buyer-email
  record, one internal-email record, and one packet-usage completion.
- An original request that already contained a timestamp retains compatibility.
- Rejected send → timestamp refresh → rejected retry → successful signing retry
  retains the same document and original fingerprint inputs; no extra PDF email
  or packet-usage charge.
- Full suite: **1,973 tests passed**. The “Invalid fixture PDF” output is an expected
  negative-fixture diagnostic. `git diff --check` passed.

Local only, not pushed or deployed. Existing live customer packets, provider
settings, and email records were not changed. This is not live SignWell/Resend
delivery verification or signed-PDF visual QA.
