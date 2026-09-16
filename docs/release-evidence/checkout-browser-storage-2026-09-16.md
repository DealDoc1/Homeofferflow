# Checkout recovery when browser storage is constrained

## Implemented locally

The buyer flow previously wrote the full offer and uploaded base64 PDFs into
session storage without handling quota or access failures. An exception stopped
checkout even though the server could accept the advertised packet size.
Subscribed generation made the same unnecessary write despite not navigating
away for payment.

Buyer checkout now attempts a verified full same-tab recovery snapshot first.
If that cannot be stored, it tries a compact snapshot containing the interview
answers, plan, receipt email and attachment filenames without attachment bytes.
The full original packet is still sent to the existing checkout API; compacting
the browser copy does not mutate the submitted documents or the open interview.
Generated/signing bookkeeping is excluded from recovery copies.

The local draft backup is saved synchronously before navigation, rather than
depending on an autosave timer. A failed optional local backup does not prevent
checkout when the same-tab snapshot was confirmed. If neither same-tab copy
can be saved and read back, no checkout request occurs: answers and files stay
open, and the UI explains how to resolve storage access instead of displaying
a raw quota exception. This preserves the pre-existing no-redirect behavior
for fully unavailable storage while improving its explanation and recovery.

Subscribed generation no longer writes this payment-return cache. Its existing
authenticated server persistence and usage/delivery confirmation remain the
source of truth. Browser storage denial cannot prevent that server request.

The payments skill guided keeping browser navigation recovery separate from
server-verified payment and fulfillment. No price, permission, signature-order,
database schema, service, provider setting or deployment configuration changed.

## Verification

- Nine new actual-source Node checkout cases pass: full cache, quota fallback,
  denied writes/reads, silent failed writes, zero available capacity, retry,
  optional local-backup failure and preservation of the full API-bound packet.
- The quota case fails against `49fd30e3`: the old flow makes zero checkout
  requests instead of continuing with a small recovery copy.
- The existing interview restore suite now has 90 passing cases. The new
  cross-flow case runs the compact cache through the actual cancelled-return
  handler and field hydrator, preserving answers and explicitly identifying
  uncached files for reattachment or deliberate removal.
- A subscriber runtime case confirms storage denial still reaches the existing
  packet endpoint and displays its verified generation/delivery result.
- Full local suite: **2,030 tests pass in 17.611 seconds**.
- All 45 inline script blocks parse; `git diff --check` passes.

## Limits and release state

Local only, not pushed or deployed. No Vercel build, live payment, customer email
or signature occurred. Tests use mocked DOM/storage/providers and do not prove
visual browser QA or live mobile/installed-app storage behavior.

A compact snapshot cannot retain files whose bytes exceeded browser capacity.
On cancellation their filenames remain visible and the prior missing-file
protection prevents silent omission. When storage access is completely denied,
the buyer must enable storage or free space before leaving this interview for
checkout; the app does not claim that unsaved work is recoverable after closing
the page. Cross-device attachment persistence is not added by this change.
