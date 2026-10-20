# Reviewed unsigned disclosure in a purchase package — implementation checkpoint

## Intended outcome and exact boundary

Let the seller complete the disclosure questionnaire once, then include those
reviewed answers, Seller execution and current Buyer acknowledgment in the
purchase package. Preserve the existing path for already-signed disclosures.
An unfinished optional disclosure must not hold other ready documents.

Production baseline is PR #1352 / afc44a9b, shell v110. This separate local branch
does not edit the pending listing PR #1353 or activate customer TXR-1101.
Automatic Git deployments remain disabled. No provider request, new invitation,
hosted database write, push/CI, preview, release, paid service or Vercel usage
query was made for this checkpoint.

## Implemented locally

`lib/purchase_disclosure_execution.py` prepares the actual approved TREC-55-1
and optional TREC-61-0 sources with the current saved seller answers. It retains
the existing source hash and v4 render/field maps; no signing geometry changed.
Long/Unicode explanations and explicit Unknown responses remain lossless on
continuation pages. These pages now show all included Seller/Purchaser initial
rows when composed for a purchase.

The planner takes authoritative owned offer/draft/review-link records, checks
current review/render versions and every seller's exact attestation, requires
matching property/units and sellers, and uses each reviewed seller's verified
email rather than a new offer alias. Buyer IDs remain 1/2; Seller IDs remain
3/4 even when Buyer 2 is absent. Reversed seller order maps explicitly to the
offer's existing identities. Distinct email destinations are required.

The returned plan includes prepared PDF hash, current review binding and a
stable answers/source/party/proof/field fingerprint. Appending preserves the
PDF and offsets the fields by the actual preceding page count. Missing,
unfinished or separately-sent disclosure is classified as not ready; wrong
ownership is rejected. Existing offer signing history cannot prepare a new
request through this helper. There is deliberately no browser/API activation
or provider send in this module.

## Verification

- 23 focused unit/regression methods passed, including all eight one/two Buyer,
  one/two Seller and water combinations, reversed roles, missing/stale/revoked
  attestations, wrong owner/property/unit, repeated email, existing request,
  missing source components, offset/hash integrity and fingerprint changes.
- The 11 new methods also passed with the actual supplied approved source
  bytes, with the source validator unmocked. The regular synthetic-source unit
  fixture patches source validation explicitly; it is not source authorization
  evidence. The actual-source run provides that coverage separately.
- Local actual-source purchase composition produced an ordinary 16-page
  package (12 purchase + 4 disclosure, 4 new fields) and a four-party/water/
  Unicode 19-page package (12 + 7, 24 new fields). Every appended page rendered
  pixel-identically before and after composition.
- Visually reviewed ordinary page 16 and four-party pages 16/18/19: Seller and
  Purchaser signature/date guides clear the captions; continuation text is
  readable; all four initial rows fit. These are local red-box placement
  guides, not completed-provider signatures, dates or customer examples.
- The first test expectation incorrectly assumed every water case was exactly
  six pages. Explicit Unknown legitimately adds a continuation; the assertion
  now requires six source pages plus the actual continuation count. Product
  preservation of Unknown was not removed to satisfy the test.
- `git diff --check` passes. No full suite is claimed for this incomplete batch.

Reproduce focused coverage:

```sh
../txr1101-runtime/bin/python -m unittest tests.test_purchase_disclosure_execution tests.test_purchase_disclosure_receipt tests.test_seller_disclosure_layout_roundtrip -q
```

Actual-source coverage additionally sets `HOF_QA_DISCLOSURE_SOURCE` and
`HOF_QA_WATER_SOURCE` to the approved private PDFs. Local specimens were generated
using `scripts/qa/prepare_purchase_disclosure_execution.py`, outside Git in the
chat's `purchase-disclosure-execution-2026-10-20` output folder. No private PDF
is committed to the repository.

## Required continuation — not deployed

Finish authenticated API/interview selection and server reconstruction; add
atomic offer-to-disclosure version binding and race/duplicate-delivery
protection in the existing journal transaction. Recheck current seller proof
at that transaction, not merely during preview. Keep draft answers private and
do not trust a browser-provided execution plan. Preserve usage accounting,
existing signed-PDF reuse and historical packets. Coordinate any additive
schema/code dependency, focused UI/API/real PostgreSQL tests, exact-head full
CI and one intentional release. Completed-provider QA is still separate;
this local work does not complete the customer feature or whole roadmap.

The separate ordinary listing test is unchanged and still waits for its
existing final electronic-consent answer/completion. No repeat request or
replacement packet was made. No further email to Tyler was sent.

## Read-only preview API and atomic binding implemented locally

The next continuation adds the authenticated
`preview_purchase_disclosure_execution` action to the existing API. It accepts
only saved offer/disclosure IDs, uses the verified session, and reconstructs
the plan from owner-scoped offer/draft reads and exact current review records.
`PurchaseDisclosureStore` verifies approved source ID, form, revision, status
and authorization readback before private server-side downloads. It makes no
write or provider call. The response is no-store, preview-only, with role/name/
email details for review; no service key, source-storage URL, raw review token
or browser-authoritative field plan is returned. Signed-out and cross-account
requests are refused; no brokerage-seat/admin gate is added. This endpoint is
not yet deployed or linked from the customer interview.

The pinned official CLI generated local migration
`20261020140935_bind_reviewed_disclosure_to_purchase.sql`. It is NOT applied
to production. It adds one FK/index and invoker-only private trigger functions,
without new client grants or replacing deployed readiness functions. At the
existing offer journal checkpoint it locks and verifies the exact disclosure,
current review/render version, property, sellers and approved recipient emails,
then binds the disclosure to that offer in the same transaction. A competing
offer, stale answers/proof or changed recipient cannot claim it. Bound facts,
review destinations/evidence and association cannot be edited or removed;
ordinary dashboard soft-delete retains the history. Optional listing binding
is detected without depending on its separate migration being applied first.

The new private `hof_purchase_disclosure_schema_readiness()` delegates the
unchanged deployed disclosure-v2 baseline and checks its own column and three
enabled guards. A disabled send guard reports not ready. No core/listing
readiness function was replaced. This contract still needs to be connected to
the coordinated release checker when customer sending is activated.

Verification: 74 focused Python/API/delivery regression methods passed in
0.554 seconds. They exercise the real HTTP handler dispatch, read-only store,
owner/auth refusal, browser override rejection, no-store response, source
readback and existing send/retry coordinator behavior using fictional services.
These are not live HTTP/provider results. The updated actual PostgreSQL runner
passed 105 assertions, including independent row-lock races for edit-first,
send-first, competing offers and both review-retirement orderings; private
grants/invoker/search-path checks; Unicode Seller; reversed parties; soft-delete;
and mutual exclusion with the listing association. The fresh cluster had no TCP
listener and stopped successfully in finally. No production advisors/schema
change is claimed from this isolated test.

The first added PostgreSQL fixture tried changing an immutable review email
after creating the link. The real existing guard correctly refused it. The
fixture now inserts the intended email initially; no guard was relaxed.
Official Supabase changelog/functions guidance was checked; this work uses no
new external feature, authentication flow, public grant or paid integration.
The CLI's normal configuration write needed filesystem escalation; only local
migration generation occurred. No production database connection was used.

No PDF source or field rectangle changed in this continuation, so the earlier
actual-source composition and changed-page visual review are reused rather
than repeated. No full suite, CI, push, hosted migration, deployment or new
signature request has been run for this still-incomplete customer batch.
Remaining: connect the purchase picker, save/preview/generate flow, existing
delivery journal and same-document retry reconstruction; nonblocking pending
document messaging; exact-head regression and coordinated release verification.
