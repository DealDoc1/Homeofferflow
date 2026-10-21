# Owner-only lease provider QA enablement - October 21, 2026

## Release scope and authority

This is an **operator QA-enablement release**, not the unfinished customer
listing rollout in draft PR 1353. It begins at actual production main
`bfd03d99beca7a13c6009b3adf1c2df7b69d12f1`. The owner's standing implementation,
SQL, push, merge and production-release authority covers this bounded work and
the already authorized fictional test inboxes. No customer/partner message,
subscription, charge or client document is authorized or changed by this slice.

Public purchase, seller disclosure, listing workspace, representation and agent
entry functions remain unchanged. Customer listing interviews/APIs/assets and
their four pending migrations are excluded. The source upload activation set
is unchanged: TXR-1101, TXR-1102, TXR-2008 and TXR-2015 do not activate customer
workflows in this release. This is not a new approval, seat or source-owner gate.
It is the same owner-only nonbinding test mechanism used for the ordinary sale
listing, extended so actual lease provider output can be inspected.

## Approved source / authorization

- TXR-1102, January 5, 2026, exact private source SHA-256
  `30ae702ee94d71fc2aec5717f0d1b6d78b4fea53b5b418f7d74b39f658e44657`.
  Its approved private source vault record is already registered and verified.
- TXR-2008, October 14, 2003, official authenticated library original SHA-256
  `c6aaeefec282b09d5981a76326c1fd4e2a317ee6b4618184c16cf14b3e57372b`.
- TXR-2015, September 1, 2025, official authenticated library original SHA-256
  `8a2439f6c191063a3abfe500d7a523e9fe9bb0265b03f663990e424ccedd3581`.

Both rental originals are downloaded and reviewed outside Git. Private source
registration follows this deploy through the existing owner admin path, not a
public bundle. Source owner authorization and owner form use attestation are
already provided; no additional agent attestation is requested. Raw source PDFs,
service credentials and signed-document access links are not committed.

## Signing plan

### Authenticated QA boundary

The canonical owner/admin session and authenticated TXR-1102 private source
registration were verified before this release preparation; hosted SQL also
confirms the source vault remains private. The existing reserved operator
signing path is already deployed for ordinary sale-listing QA. Focused tests
prove the added lease action requires both the approved owner identity and
platform-admin status before any source read, with all source downloads kept
server-side. This does **not** claim an authenticated invocation of the new
lease control before its deployment: that canonical check remains an explicit
post-deploy step before provider output can be called verified.

One ordinary fictional transaction uses the real TXR-1102/2015/2008 maps and
composer: 14 pages, 44 fields, four landlord exact-one choice groups and two
conditional explanations. Landlord QA Signer A uses andrewchri@gmail.com;
associate QA Signer B uses brewbqinfo@gmail.com. No second landlord or tenant is
invented. Both invitations are simultaneous, test mode and private draft are
fixed, reminders and extra signature page are off. Tenant signatures/receipt and
lead pamphlet/report delivery remain explicitly unfinished by this landlord test.

The approved-owner/platform-admin checks run before source reads. Source
metadata/path/hash and downloaded bytes are independently validated. The
existing journal reserves one durable attempt before provider creation and
readback verifies fields, groups and rules before invitations. Recorded or
ambiguous attempts are never blindly recreated. The new check-first owner
control cannot fall back to a purchase test for an unknown scope.

## Rendered signed-PDF QA boundary

Offline ordinary, branch, sole-landlord and long/Unicode proof pages were
reviewed on the full candidate; the exact ordinary specimen's primary execution,
flood, lead/lower associate signature and detail pages were reviewed again.
Exact semantic layout pin:
`43da47ab3b15cb1c0f1d3ed238690684c10628d0b3f48b64ec87fbdff3adbd74`.
Reviewed renderer tree: `3d912b0c837df38ed879bb3b289036e977fe7b80`.
The code/maps are byte-identical to the already-reviewed preparation slice.

**Completed signature visual QA is not claimed.** Actual completed SignWell PDF
inspection is the downstream result this nonbinding operator-only release
enables. No customer TXR-1102 workflow is made live before that result. The
existing ordinary sale-listing test is separate and must not be resent or called
complete based on earlier seller-disclosure QA.

## Coordinated private-source schema

Only the private source catalog expands from 20 to 22 codes. The SQL adds a
service-only invoker readiness RPC; all existing standalone codes, grants,
policies, private Storage and customer drafts are unchanged. It uses a bounded
5-second lock timeout. The production release checker also requires this exact
rental-source contract so source intake cannot ship against the old constraint.

The pinned Supabase CLI generated the local migration at 20261021112850. The
hosted migration tool applied the identical SQL and assigned authoritative
history version **20261021113432**; the file was renamed to match that actual
version without changing SQL bytes. No migration history was edited manually.

Hosted verification after application:

- `hof_rental_source_schema_readiness`: ready, no missing capabilities,
  `homeofferflow-rental-source-schema-v1`.
- Existing `hof_seller_disclosure_schema_readiness`: ready, no missing
  capabilities, unchanged `homeofferflow-release-schema-v2`.
- Existing 14 standalone codes unchanged; source constraint validated.
- Source grants identical before/after, source RLS true, source bucket not
  public. Readiness execute is denied to anon/authenticated and allowed only
  to service_role. No new security advisor findings (same two pre-existing).

The Supabase/Postgres skills guided least privilege, short locks, exact schema/
API allowlists and real verification. No new customer binding/draft migrations
were installed. Source-only schema expansion is backwards compatible with the
current app while this coordinated QA code release is verified.

## Regression and release checks

Initial affected-source checks: 89 tests passed. Source/readiness/operator
focused checks after the catalog adapter: 46 tests passed. Companion/PWA/source
foundation checks: 74 tests passed. These overlapping runs are not summed.
The fixed source maps match their preparation fingerprints. Isolated actual
PostgreSQL passes **36 assertions**, with no TCP/cloud access: all 22 source
codes, invalid code rejection, unchanged grants/RLS, service-only invoker RPC,
missing/unvalidated constraint failure and validated-catalog recovery.

`scripts/preflight_supabase_branch.py` reports 122 migrations, no errors.
`git diff --check` passes. Full exact-candidate regression and CI follow the
freeze; do not infer their result from focused checks. Source files and QA
operator UI are unchanged from the previously reviewed local output; no new
PDF geometry or invitation is introduced during release preparation.

The frozen local run at `cf9dae0b` finished 2,914 tests in 107.456 seconds with
two optional-source skips. Its only failure was the companion's stale v112
assertion after the intentional v113 cache bump. That one test assertion was
corrected without changing application code or maps. Focused PWA/companion
checks and exact corrected-head CI provide the final result; the failed run is
not reported as a full pass. PR 1355 is the isolated release; PR 1353 remains
the separate unfinished customer candidate. No second local full run is needed
for that test-only correction. The earlier superseded CI run is cancelled to
avoid spending runner time on a known stale assertion.

## Deployment decision

Ready scope: owner-only fictional provider QA and private source registration,
after exact-head CI and the existing intentional production workflow pass.
Ready for customer lease-listing release: **no**, until provider output is
completed and inspected and the separate customer release is verified.

Keep Git deployments disabled. No routine previews or repeated usage checks.
Use the existing prebuilt workflow's one capacity/spend safety check immediately
before the intentional release. Shell v113 refreshes the admin control only;
no private PDF/API response is cached. The full customer candidate will need
its next shell version when reconciled with this release.

Rollback: previous immutable application deployment; the additive private
catalog can stay installed safely. Do not delete source records or narrow a
constraint over newly registered data as a rollback shortcut. Post-deploy work:
canonical owner check, private rental source registration, one necessary fixed
test, provider completion and actual signed-PDF inspection. Report each state
separately and leave the broader roadmap goal active.
