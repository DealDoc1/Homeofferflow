# Buyer QA retained draft and send diagnostics

## Outcome and verified state

Bounded outcome: inspect the already-created fictional buyer packet without
crashing, and preserve sanitized diagnostics when a verified draft cannot be
sent. Scope: operator readback and failed-send receipt only. No customer API,
PDF, recipient, completion control, migration, or send transport change.

Canonical production was independently verified READY on November 27:
`aeda19c33dffea3add04b50994ca826f4e1e7963`, deployment
`dpl_H4S48GWWLUyzjG9Yec4oWa9mSJM5` (PR #1485). That correction allowed
creation of document `fdaf5aae-6ddd-48af-a76d-d1dc0e2d4136`, named
`QA ONLY - ordinary buyer package omit empty groups - 0e1e390bbd32`.
The existing coordinator verified its fields and completion controls before
one send call returned HTTP 422. No invitation or completed signing is claimed.

Read-only database verification found run
`da451911-ec05-47bd-a6ea-7a574b5f1774` still running/unconfirmed, with this
document ID, HTTP 422 and controls_verified=true. Its complete row MD5 is
`b960d6c6faf090e908bc64bfeee98190`. The original three rows remain byte-for-byte
unchanged under the same to_jsonb(row)::text fingerprint:

| Run | MD5 |
| --- | --- |
| 2c38dbb9-3f73-49df-8959-a8a711d47495 | f674613eaa31639e59b8c779ed05016a |
| 2ed84357-abe7-4ab3-9277-0fa26c4f4865 | 28e063a22ddab6f04c75577d50d87215 |
| 5fdf7dec-b22f-464f-a711-5c5132c4b486 | 7e40814fd6af84b8eafd62d159c03544 |

## Local correction and verification

Readback had a direct lookup of optional checkbox_groups even though the
corrected payload omits that key. Normalize absent optional groups/rules in a
local copy. Unexpected actual controls still fail validation, and the source
payload is not mutated. Failed sends now retain the existing value-free
rejection diagnostic alongside HTTP status. No retry or reservation reset is
introduced. Past provider response bodies cannot be reconstructed.

38 focused tests passed, zero skips, using the preserved actual blank sources:

```sh
python -m unittest tests.test_signwell_qa_readback \
  tests.test_buyer_empty_groups_qa tests.test_signwell_rejections \
  tests.test_buyer_qa_release_boundary tests.test_signwell_controls -q
```

git diff --check passed. Tests exercise missing controls, unexpected returned
controls, payload immutability, and a single failed send retaining only bounded
field names rather than recipient values. No PDF or UI markup changed.

The actual corrected recipe's send_options passed the official SDK's
UpdateDocumentAndSendRequest model at SDK revision
`7d6811135600b4426b22904d5432ff1f2f39e0ed`; all supplied names are known model
fields: apply_signing_order, metadata, name, reminders, subject, test_mode.
The current official contract also supports these fields:
https://developers.signwell.com/reference/senddocument
This rules out an obvious schema mismatch; it does not explain the live 422.

## Release boundary and next action

These diagnostic corrections are locally tested, not deployed. No new provider
request, signing action, email, database write, preview or deployment occurred
during this follow-up. Automatic Git deployments remain disabled. Batch this
with a justified send correction after provider evidence, then run the full
release suite and current capacity/cost gates once for that candidate.

Preserve this exact draft and all reservations. The original send response
was not retained beyond status, so obtain provider-side details for this
document before changing or retrying the request. An unsent support follow-up
is in docs/support/signwell-buyer-send-followup-2026-11-27.md. Sending requires
the owner's instruction; prior approval covered the original support request.
