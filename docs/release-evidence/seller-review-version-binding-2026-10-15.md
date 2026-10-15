# Disclosure review must match the content being signed

## Batch contract

- Outcome: changing a disclosure cannot reuse an earlier Seller's review.
- Scope: existing draft/review API, revision guards and conditional writes;
  no new customer step, agent access gate, source, form artwork or signer map.
- Production baseline remains e15c5db / READY dpl_47tztcZ7rgRmvVYvdCdLUubDpBSz
  from the preceding independent project read. This candidate is not deployed.
- Cost: pinned local PostgreSQL runtime only, no hosted branch, deployment,
  invitation, charge or production write. One live read inspected schema column
  names/types, not customer content. No credentials were read or exported.
- Required evidence: actual stale-review API cases and real concurrent database
  save/review orderings, preserving history and private access; final regression.

## Defect and repair

The old aggregate matcher accepted names, seller positions and prior completion
timestamps alone. An agent save reset only the boolean; old completed links
could restore review after answers changed. Also, saving a reviewed draft did
not clear the other two fields coupled to that boolean by the database check.

The new database-generated UUID identifies a particular draft content version.
It rotates on party, address, answer or source-reference/revision changes,
including changing back to old answers. Delivery-journal-only writes and no-op
saves retain that version. All four cached review fields clear atomically when
content changes. A caller cannot assign the version, forge a reviewed insert or
set its own review approval. Existing ownership policies remain in force.

New review links capture that exact UUID plus the current render revision.
Old unversioned links remain audit history, not new authorization. Identity,
party assignment and review versions cannot be rebound. Completion checks both
the assigned and entered Seller names. Each Seller needs their own evidence;
revoked, partial, stale or different-layout reviews do not qualify.

The database locks the parent draft during new-link creation or first
attestation. A concurrent edit either occurs first and rejects the stale review,
or occurs afterwards and invalidates it. Completed evidence is retained rather
than erased. Aggregate review writes use a version condition and the database
revalidates every Seller; a zero-row write is never reported as success.

The preview checks the review version again when loading its draft. Signing
rechecks durable per-Seller evidence rather than trusting the boolean, binds
rendering to the selected version and keeps the existing version-scoped delivery
checkpoint. Content cannot change once a provider request/journal is tracked.
An ordinary Save cannot erase a tracked document ID or its delivery journal,
including a Save that loses a race to creation of the signing checkpoint.
Invitations stay simultaneous. Existing signup, pricing and Google address
completion are untouched. The logic remains behind the API for future app reuse.

## Evidence

- 58 focused tests passed in 0.638s. Thirteen new tests cover exact/current and
  stale evidence, all-Seller completion, stale-session/PDF rejection, conditional
  aggregate updates, zero-row attestation failure, current-content link creation,
  successful attestation, reviewed-save constraint fields and cached-true no-send.
  External services are fictional mocks. No provider or email was contacted.
- The first broader regression exposed three older send-contract fixtures
  that supplied only a cached reviewed flag and no actual versioned evidence.
  Those fixtures now supply current per-Seller evidence and still exercise the
  real delivery coordinator, changed-provider-field rejection and reuse of the
  existing provider ID after a rejected send. The safeguard was not bypassed.
  All 63 affected checks passed after this test-fixture update. Final full-suite
  rerun is tracked separately from the first unsuccessful broader run.
- That candidate then passed all 2,680 tests in 88.249s, one environment skip.
  Final inspection additionally closed a related persistence gap: the corrected
  reviewed-save path must not erase an already tracked signing request on a
  no-op save. Added API/database retention guards and two focused tests; the
  final frozen candidate includes these changes, not just the earlier result.
  All 65 final focused checks passed in 0.732s. No behavior was weakened to make
  old fixtures pass; the tests now represent actual current review evidence.
- Actual migration executed successfully against isolated synthetic PostgreSQL
  tables. 40 final assertions passed, including nine content-change categories,
  forged approvals, no-op writes, history, function privacy and five independent
  backend connections. Both concurrent orderings were verified by observing a
  real row-lock wait, not a timer or sequential simulation. Local cluster had
  no TCP listener and stopped in finally; production remained unchanged.
- Standalone migration-chain preflight passed with 119 ordered nonempty files;
  patch whitespace passed. The migration was created with the installed CLI's
  migration-new command, not an invented timestamp.
- Supabase guidance was used for transaction/locking boundaries and invoker
  privileges. Current function documentation was read; the same-day cached
  changelog was scanned for relevant breaking changes. The markdown web fetch
  was unsupported; no SDK, TLS setting or extension change was introduced.
- Final frozen candidate: 2,682 tests in 89.873s, OK with one environment skip,
  process exit zero. The intentional invalid-PDF negative fixture diagnostic
  after the successful summary is not a failed test. Whitespace also passed.
- Existing draft PR #1341 previous head 6307582 independently passed GitHub
  tests, with hosted Supabase Preview skipped. That result is prior-head
  evidence, not independent CI proof of this newer review-binding checkpoint.

## Release requirements and remaining work

Migration 20261015164510_seller_disclosure_review_revision_binding.sql and this
API must release together. Do not apply this behavior-changing migration alone:
older API instances do not bind new links to a revision. Preserve the previous
code/schema state until the coordinated deployment is ready; a rollback to old
API code alone is not a compatible review workflow. Before release, verify the
exact production schema, service-role-only link permissions and invoker trigger
functions with readback/advisors; run an authenticated fictional review-to-send
test against the deployed pair. Those are not yet production-verified.

No source PDF or signing rectangle changed in this batch, so it does not claim
new PDF placement or completed-provider QA. The related disclosure candidate
still needs remaining main/water answer placement, scalar coverage and the
integrated completed-signature specimen before release. Sale/lease listing
agreements and broker-admin onboarding remain separate unfinished roadmap work.
