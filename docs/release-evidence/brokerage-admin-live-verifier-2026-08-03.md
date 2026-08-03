# Brokerage-admin live verifier — 2026-08-03

## What changed

Added `scripts/verify_brokerage_admin_live.py`, a read-only smoke test for an
authenticated brokerage-admin session. It checks the brokerage identity,
aggregate activity metrics, roster presence, source-readiness metadata, and
the privacy contract that buyer details, property details, offer terms, and
document contents are excluded.

The command does not create invitations, change membership, update branding,
or read individual offer terms.

## Verification

- Dedicated verifier tests: 2 passed.
- Full repository suite: 378 tests passed.
- Live authenticated QA is still pending because it requires an existing
  brokerage-admin access token; this command is ready for that read-only run.
