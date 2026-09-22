# Brokerage roster form-gate cleanup — 2026-09-21

## User problem

The brokerage roster still displayed a `TXR/NAR attestation` column and the
browser bundle retained an unused brokerage-authorization save function. The
released shared library no longer requires either a brokerage seat or a
per-use agent attestation, so those leftovers created unnecessary noise and
could make a broker think they controlled an agent's shared-form access.

## Candidate change

- Remove the obsolete attestation column from the brokerage roster.
- Remove the unused browser-side brokerage-authorization save function and the
  unused authorization fields from the brokerage shell query.
- Keep historical attestation fields and server-side records intact for audit
  history; this change does not delete or rewrite any data.
- Preserve the truthful brokerage message that shared forms are available to
  every signed-in agent without broker action.
- Preserve the separate platform-admin universal-library maintenance tool for
  recording exact source revisions; it remains an internal maintenance tool,
  not an agent or brokerage access gate.

## Verification

- 73 focused brokerage, access-scope, admin, and authorization tests passed.
- Static regression checks confirm the browser bundle no longer contains the
  obsolete save action, authorization fields, roster heading, or `Not yet
  attested` status.
- Full repository suite: 2,385 tests passed in 71.452 seconds.

## Release status

Implemented and focused-test verified. This cleanup is not production-live
until the single coordinated post-reset release completes and the authenticated
brokerage roster is checked on the canonical site.
