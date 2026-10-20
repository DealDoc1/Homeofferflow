# TXR-1102 private draft and signing API — local checkpoint, October 20, 2026

Status: implemented and tested locally, **not deployed**. This is the API/schema
slice of the lease-listing workstream, following renderer commit `ad829ac8`.
Production baseline for this slice is `bfd03d99` / shell v112. No hosted schema,
provider records, emails, invitations or deployments were changed.

## Behavior

- Reuse the existing authenticated standalone-agreement API. Add strict
  TXR-1102 create/edit, same-draft reopen, private preview and landlord signing
  contacts. Saved broker notice contacts and approved profile aliases supply
  defaults only; document ownership remains the actual authenticated login.
- Share the existing confirmed-save and optimistic edit logic with TXR-1101.
  Wrong-owner, wrong-form, stale-version and tracked-document edits fail.
  An empty or mismatching database response is never reported as a saved draft.
- Dispatch to the exact-source lease renderer/map; do not reuse sale-listing
  fees, foreign-person questions, PDF overlays or sale lead-disclosure geometry.
  Bind the lease render and signing revisions to the existing delivery journal.
- Preserve simultaneous invitations, verified provider draft fields/contacts,
  and recovery using the same provider ID. Inspect failure followed by retry
  creates one fictional provider document and sends once in isolated tests.
- Keep the larger interview request allowance bounded to named listing actions.
  Do not widen unrelated API action body limits.
- Add migration `20261020231654_add_txr1102_lease_listing_drafts.sql`, generated
  using the pinned Supabase CLI. It extends only the form-code constraint and
  adds a private invoker-only lease-readiness probe; existing v1/v2/v3 contracts,
  RLS, policies and table grants remain unchanged. The migration is unapplied.

## Verification

Focused command (private source stays outside Git):

```sh
HOF_TXR1102_SOURCE='../listing-source-2026-10-17/sources/TXR-1102-2026-01-05.pdf' \
  ../txr1101-runtime/bin/python -m unittest \
  tests.test_txr1102_api tests.test_txr1101_api \
  tests.test_standalone_recipient_preview tests.test_standalone_form_schema_contract \
  tests.test_txr_render_send_snapshot tests.test_txr_1102 tests.test_txr_1101 \
  tests.test_listing_packet -q
```

Result: 146 tests, four unrelated opt-in skips, exit 0. Both real-source lease
API tests ran: Unicode/continuation preview plus tracked delivery, and rejection
of altered source bytes before any provider creation. Delivery uses isolated
HTTP transport; no real SignWell call was made. The test-suite IABS-error log
is an intentional negative-path assertion, not a production error.

Actual PostgreSQL command:

```sh
HOF_PG_QA_MODULES="$PWD/scripts/qa/postgres-runtime/node_modules" \
  /opt/homebrew/bin/node scripts/qa/check_lease_listing_schema.cjs
```

Result: 36 assertions, exit 0. The isolated database had no TCP listener and
accepted no external connection string. Tests exercised the actual migration,
all 16 allowed form codes, invalid-code rejection, owner-only insertion and
visibility, unchanged policy/privilege snapshots, private invoker function
grants, baseline failure propagation, missing and unvalidated constraints.
The core readiness function is an explicit fixture; this is not proof of a
complete production migration installation. Temporary database files were
removed after clean shutdown.

Renderer geometry and its three local PDF proofs are unchanged. Their visual
review is recorded in [the renderer checkpoint](txr1102-renderer-local-2026-10-20.md).
No duplicate PDF rendering or full regression suite was run for this nonrelease
API checkpoint. Supabase changelog/docs and least-privilege guidance were checked.

## Remaining lease-listing work — not blockers requiring the owner

1. Connect the simple lease-listing interview and same-draft queue handoff.
2. Compose the actual applicable related documents with explicit included versus
   pending status; never label requested addenda as attached when absent. Do not
   use the sale-only lead disclosure as a rental disclosure.
3. Connect the additive lease-readiness probe to the coordinated release check.
4. Complete affected mobile/desktop and provider-rendering QA, then exact-head
   CI/full regression and one coordinated production release with the migration.

No new sign-in, source-owner or brokerage-seat approval was requested. Existing
separate packet-specific consent questions were not replayed or assumed answered.
No Vercel usage polling or Tyler email work was performed.
