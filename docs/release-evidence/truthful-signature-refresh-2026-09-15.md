# Signature status accuracy — September 15, 2026

## Findings and changes

- The status API previously interpreted a created/draft document as awaiting
  signature and persisted standalone agreements/disclosures as sent. It now
  preserves draft status and displays **Draft - not sent**.
- Substring matching could interpret "unsigned" or "not completed" as
  completed. Exact known statuses replace those success assumptions.
- SignWell's pending/in-progress state and its individual-signer signed event
  are not whole-document completion. A completed-PDF download requires explicit
  document-level completion; partial or missing recipient rows cannot unlock it.
- Unknown/empty provider states return a recoverable error before any database
  write, preserving the saved state instead of inventing an awaiting status.
- The active workspace no longer classifies "Partially Signed" as completed.
  Canonical current status takes precedence over historical nested responses.
- An agreement with an existing provider ID can refresh status even when its
  local state is draft/failed; its send button cannot create another request.
- Cancelled standalone agreements/disclosures map to the existing void state.

## Verification

Full local suite: **1,775 tests passed**. Eight new Node runtime tests execute
the real API handler, both dashboard normalizers, and active workspace
classifiers. The test HTTP adapter checks owner filters and captures exact
database update payloads for purchase offers, standalone agreements, and
seller disclosures. It also verifies unknown states make zero writes, denied
owners never reach SignWell, and incomplete documents never request a completed
PDF. All provider calls in this test path are reads.

Existing regression assertions were updated where they encoded the incorrect
Created-is-sent assumption or the previous status-expression text. The new
runtime assertions verify behavior rather than only source strings.

No production database query, migration, real email, signature send, document
cancellation, physical-device QA, or production verification occurred.
Schema values remain within the existing checked-in lifecycle constraints.
No subscription prices, legal text, form data, signer geometry, access rules,
or Google Maps autocomplete change.

## Source checks

Reviewed the Supabase changelog and update guidance before the status-write
work. No current relevant Data API breaking change was found. Owner filters
remain required on each read and write; no service key reaches the browser.

SignWell distinguishes an unsent draft, signing progress, per-signer signing,
and a completed document in its
[status guide](https://help.signwell.com/article/297-types-of-document-statuses)
and [events reference](https://developers.signwell.com/reference/events).

## Remaining delivery-recovery work

The send routes still need a durable provider-ID checkpoint before their final
send and a verified existing-document recovery path for ambiguous failures.
This status correction is a prerequisite, not a claim that those timeout,
concurrent-send, or lost-tracking-ID cases are repaired. No existing customer
packet was changed. Keep that work in progress in the daily report.

## Release boundary

Stacked after PR #1229. Await the same bundled release under the user's
no-overage constraint; no Vercel build or deployment is requested here.
