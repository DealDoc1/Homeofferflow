# Prepared listing package reconciled to current production

## Scope and evidence baseline

Continue the active full roadmap, not a smaller substitute. Previous goal work
made production progress: PR #1351 deployed completed-disclosure reuse in
purchase offers. This batch makes the preserved TXR-1101/listing implementation
compatible with that current production instead of replaying or replacing it.
Production baseline is `4bd1cce57f052a587d6017d8782204ef521dfa41`, shell v109.
The listing candidate reserves v110 and retains both listing assets plus the
new saved-disclosure component, PDF access, contrast and buyer receipt logic.

## Actual integration and schema correction

Merged current protected main into `codex/listing-package-integrated`, preserving
the prepared source-backed TXR-1101 interview, IABS/lead/disclosure/water packet
composition, safe repeated-send recovery and atomic content/version binding.
Two already-applied disclosure migrations are identical to current main; the
original questionnaire variant that dropped the legacy pending-link index was
not retained or applied.

Live read-only SQL confirms disclosure v2 readiness true, TXR-1101 not yet in
the persisted-code constraint, no listing-binding function and no
signature_packet_id column. Neither listing migration is live. The unapplied
TXR-1101 migration now changes only its form-code constraint. The unapplied
binding migration adds a private v3 readiness wrapper that delegates the live
v2 contract and checks the new form, binding column and enabled guard triggers.
It does not replace either deployed readiness function. The release checker
verifies v3 plus both old disclosure and new binding columns with zero-row probes.

No RLS/permission expansion, source-owner or brokerage-seat requirement, new
credential, production DDL, provider request, invitation or Vercel release.
The existing pinned PostgreSQL runtime was located under
scripts/qa/postgres-runtime/node_modules; it was reused, not reinstalled.

## Verification actually completed

- 147 focused checks passed in 15.184s against the real supplied TXR-1101 PDF,
  source/API/composer, interview runtime, existing disclosure and purchase reuse,
  readiness and PWA behavior. The expected unavailable-IABS negative fixture
  logged its diagnostic after an OK result; no failed product run is hidden.
- 74 assertions passed against actual migrations and independent PostgreSQL
  connections in a fresh private Unix-socket cluster, with no TCP listener or
  production credentials. Includes forged/stale bindings, edit/send lock races,
  same-draft replay, legacy index retention, immutable core readiness, private
  v3 grants and refusal to report ready with its signing guard disabled.
- The runner closed clients and stopped PostgreSQL in finally. No hosted
  schema, real client record, source file or user permissions changed.
- Patch whitespace is clean. Full regression is deliberately not rerun on this
  unfinished release candidate. Source signing geometry is unchanged by this
  merge; no new rendered or completed-provider result is invented.

## Next work and truthful remaining scope

The existing v4 disclosure completion is resolved, not blocked on source or
another signature. The listing agreement and corrected listing-lead provider
behavior still need their actual provider checks. Do not send the old multi-case
stress bundle as a customer-shaped example or relabel local guides completed.
Prepare an ordinary, clearly fictional package for the remaining provider work,
register the already-authorized source privately, then freeze and coordinate
the two pending listing migrations/code/source release with one spend-checked
deployment. Unsigned combined purchase execution and TXR-1102 remain separate.

Broad goal stays active. This is verified integration progress, not a customer
deployment, completed whole Seller suite, or request for blanket approval.
