# Listing and purchase disclosure reconciliation — local checkpoint

## Boundary

Reconciles the preserved `codex/listing-package-integrated` / draft PR #1353
with production PR #1354, `bfd03d99beca7a13c6009b3adf1c2df7b69d12f1`.
Production is shell v112. The future combined listing candidate reserves v113;
the worker never automatically reloads an in-progress interview.

No production code, schema, customer packet, source PDF, email, signing
invitation, account permission, billing or Vercel deployment changed here.
The existing ordinary listing QA packet is unchanged. Its final electronic
consent/completed-PDF review remains separate; no repeat question or resend.

## Resolved integration

- Preserve both disclosure association fields in owner APIs and saved lists.
- Listing choices exclude purchase-bound disclosures. Current selection is
  checked again server-side; a now-bound disclosure becomes explicitly pending
  without holding up the other ready listing documents.
- Either association prevents a second standalone signing request, editing
  through the owner adapter, or reopening a questionnaire for changed answers.
- Customer saved-list labels distinguish listing and purchase packages without
  exposing internal field names.
- Preserve both readiness checks: listing v3 plus the deployed independent
  purchase v1 contract and zero-row column probes. Neither existing baseline
  readiness function is replaced.
- Strengthen only the unapplied listing binding migration: mutual exclusion,
  checkpoint-only association, retained bound draft and seller proof, private
  invoker-only guard, and readiness failure if that guard is disabled. The
  already-applied purchase migration is byte-for-byte unchanged.

## Evidence

Focused modules: 133 tests, one source opt-in skip; listing/API/interview and
source planner modules: 99 tests, four source opt-in skips. Additional focused
adapter/signing tests after adding cross-package regressions: 84 tests, two
source opt-in skips. These are overlapping groups, not a summed unique count.
All completed successfully. No actual HTTP provider call was made.

Actual isolated PostgreSQL: 153 assertions passed with production upgrade
order; 153 passed with chronological fresh-install order. Includes real
cross-package lock contention in both winner orders, proof retirement races,
late edits, preserved association/history, private function access, disabled
guard readiness failure, and view timestamps under a held parent-row lock.
No TCP listener or production credential accepted; clusters stopped in finally.
The first sandboxed initdb failed on local shared-memory permission before
starting a server; authorized local execution then passed.

Signer geometry matches the approved baseline. No change to TXR-1101,
listing-lead or seller-disclosure renderer/rectangle files; repeated PDF
rendering/signing is unnecessary for this merge-only correction. Existing
ordinary, branched and Unicode placement evidence remains applicable to the
unchanged maps. Final completed ordinary listing dates are not yet verified.
Schema branch preflight passes with 123 migration files, no errors. Patch
whitespace passes. Final full regression: 2,932 tests in 97.376 seconds,
seven environment/source opt-in skips, exit zero. Expected negative-fixture
diagnostics (invalid fixture PDF, synthetic failed email/API and preflight
rejections) were not live failures. The isolated PostgreSQL harness passed
again in production-upgrade order after its fresh-install option was added.

Reproduce from this checkout using the existing `../txr1101-runtime/bin/python`:
`-m unittest discover -s tests -q`, `scripts/check_txr_signwell_geometry_baseline.py`
and `scripts/preflight_supabase_branch.py`. The real PostgreSQL checks use
`HOF_PG_QA_MODULES` set to this checkout's pinned
`scripts/qa/postgres-runtime/node_modules`, then
`node scripts/qa/check_seller_review_revision_concurrency.cjs` with and without
`--listing-first`.

## Next release boundary

Do not apply the listing migrations or publish this customer workflow merely
because local integration passes. After the existing ordinary listing test is
finalized, inspect its completed PDF, update the exact evidence and run final
exact-head CI on this reconciled tree. Keep both listing migrations coordinated
with that one intentional customer release. Reuse the existing provider test;
do not create another multi-case stress packet or add a brokerage-seat gate.
