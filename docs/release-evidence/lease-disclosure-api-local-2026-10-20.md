# Rental disclosures in the lease package API — October 20, 2026

Status: **implemented locally, affected-workflow tested, browser reviewed**.
Follows adapter checkpoint `506dfdb2`. Not deployed; no new source uploads,
hosted migration, signing invitations or actual provider-completed QA occurred.
The documented production baseline remains `bfd03d99` / shell v112. No Vercel
usage check, preview or code deployment was performed for this checkpoint.

## Connected user outcome

The existing lease-listing preview and send paths now compose the actual rental
flood and applicable lease lead disclosures, instead of always reporting them as
pending. This is not a parallel intake or delivery system. They retain the
existing actual-account IABS, owner/version guards, reviewed-package binding,
simultaneous recipients and durable one-provider-document retry journal.

- Approved universal source lookup stays server-side. Each component requires
  the exact form/revision/hash, approval and attestation, private bucket and a
  valid source-host-owned path. Downloaded bytes are checked independently
  before entering the reviewed adapter. Neither source office identity nor
  private storage metadata is returned to the customer or signing recipients.
- Genuine source absence/404 stays pending without stopping the primary listing.
  Temporary storage failure, corrupt/altered bytes or a mismatching returned
  source record is a visible error, not a false missing-file result. A source
  becoming available or being reapproved invalidates a previous package review
  before a different document can be sent.
- Rental flood is automatically selected. Confirmed pre-1978 homes include the
  lease lead form when its source exists. Unknown age keeps it pending for age
  confirmation; a confirmed newer home removes a stale lead checklist selection
  in both server and client contracts. Automatically selected disclosures are
  shown as read-only checklist items, not controls that immediately recheck
  themselves after a user tries to clear them.
- The prepared document manifest carries remaining actions, bound into the
  package fingerprint. Send review shows concise, deduplicated tenant
  receipt/signature and lead pamphlet/report steps separately from what is
  included. It does not claim tenant receipt, completed tenant signing, report
  delivery or pamphlet delivery merely because landlord documents are included.
- Add TXR-2008/TXR-2015 to the existing admin intake/catalog allowlists. Their
  save message identifies lease-package components, not independent workflows.
  TXR-1102 intake metadata now matches the customer workflow in this pending
  release. No new per-agent attestation, seat or source-owner requirement exists.

## Coordinated database contract

Generated with the existing pinned Supabase CLI **2.81.3**:
`20261021034227_add_lease_disclosure_source_codes.sql`.
It remains **unapplied**. It retains all 20 live source codes and adds only the
two rental components, leaving standalone agreement codes, RLS, storage and
table grants unchanged. The private invoker-only lease-readiness function now
also requires the validated source-code constraint. Existing applied release
v1/v2/v3 functions are not replaced. The existing release script already calls
the lease contract, so the migration cannot be silently omitted at release.

The Supabase/Postgres skills guided least-privilege review, bounded lock timeout
and matching API/database allowlists. A read-only production constraint query
established the 20-code baseline. The newer cached CLI could not initialize its
telemetry file inside the sandbox; the already installed pinned 2.81.3 CLI
generated the migration normally, without a package upgrade or global setting
change. Local migration-name/order preflight reports 125 migrations, no errors.

## Evidence

```sh
HOF_LEASE_DISCLOSURE_SOURCES='../lease-listing-2026-10-20/sources' \
HOF_TXR1102_SOURCE='../listing-source-2026-10-17/sources/TXR-1102-2026-01-05.pdf' \
  ../txr1101-runtime/bin/python -m unittest \
  tests.test_txr1102_api tests.test_txr1101_api tests.test_lease_disclosures \
  tests.test_lease_listing_packet tests.test_listing_packet \
  tests.test_platform_form_source_upload tests.test_brokerage_form_source_foundation \
  tests.test_txr1102_interview_runtime tests.test_txr1101_interview_runtime \
  tests.test_txr_1102 tests.test_production_schema_readiness \
  tests.test_standalone_form_schema_contract -q
```

**201 tests pass, three unrelated source opt-in skips, exit 0.** The IABS failure
log is an intentional negative-path check. Six customer-summary Node cases also
pass (already exercised by the Python runtime wrapper, not six extra workflow
tests). All 47 executable inline scripts compile. `git diff --check` passes.
After strengthening the actual-component test to use the real primary TXR-1102
source as well, that exact test was rerun and passed: all three private sources
flow through composition, first provider-inspection failure and retry against
one fictional provider ID, with one eventual send and only landlord/broker roles.

API checks include declared/downloaded hash mismatch, private path traversal,
unapproved/changed revisions, missing versus transient storage errors, source
availability/reapproval changing review, unknown/newer age, field/control page
offsets, absent tenant acknowledgements, provider control rejection and tracked
retry. Synthetic source tests replace only test pins/footer removal; real
private-source tests cover the actual source adapters. All HTTP is isolated
fictional transport, not live SignWell or hosted end-to-end execution.

```sh
HOF_PG_QA_MODULES="$PWD/scripts/qa/postgres-runtime/node_modules" \
  /opt/homebrew/bin/node scripts/qa/check_lease_listing_schema.cjs
```

**68 real isolated PostgreSQL assertions pass.** Source/standalone permissions
and RLS are unchanged; all 22 source codes and 16 standalone codes are tested,
components cannot become standalone drafts, unknown codes fail, anonymous and
ordinary clients cannot read the private source table or invoke readiness,
baseline/missing/unvalidated constraints fail readiness, and the validated
catalog restores it. No TCP listener or cloud connection is accepted. The
sandbox's shared-memory restriction required running this isolated test with
the normal local-process allowance; its temporary database shut down and was
removed. This does not prove a full hosted migration installation.

Browser verification used the actual extracted UI with synthetic API responses:
desktop and 390×844 phone send review shows a 15-page listing/IABS/flood/lead
package plus concise follow-up, without horizontal overflow or JavaScript
errors. Phone button bottom is within 844px. In the saved interview, Yes→No
clears lead selection while flood remains selected; No→Not yet confirmed
requests lead again. No draft was saved and no final send button was clicked.
The fixture also refuses all signing sends. Temporary tab/server were closed
and the viewport override reset. Screenshots:
`../lease-listing-2026-10-20/component-ui/{desktop,mobile}-send-review.jpg`.
PDF source geometry is unchanged from its reviewed nine-page proof set; only
remaining-action copy changed, so no duplicate PDF authoring/rendering was done.

## Remaining release work

1. Complete actual provider-rendering QA for the new source-specific fields,
   including the shorter TXR-2008 lower signature rows. Local HTTP/PDF tests
   are not a completed-provider signing result.
2. Freeze the coordinated candidate, full exact-head regression/CI once, apply
   pending code/schema together, and register the two already-downloaded rental
   source files privately through the existing admin path. They are not yet
   hosted; TXR-1102 itself is already registered. No owner/source approval is
   missing. Preserve true pending status during source installation.
3. Verify canonical source-backed preview/send/retry and the actual public
   release before calling the lease workflow live. The lead pamphlet and listed
   reports still require delivery at tenant execution; do not infer receipt or
   consider that later tenant-participation workflow implemented by this slice.

Broad roadmap goal remains active. No hosted write, paid-service change,
invitation, email or deployment occurred in this integration checkpoint.
