# Brokerage role gate and IABS hardening — release evidence

## Scope

This batch does not change any contract PDF, form source, field mapping,
packet assembly, signer routing, or signature placement.

Changed runtime behavior is limited to:

- Showing restricted Texas REALTORS® draft cards to active authenticated
  brokerage roles that the server already permits (`agent`, `broker`,
  `broker_admin`, `brokerage_admin`, `owner`, and `team_lead`).
- Preserving the brokerage authorization gate, private approved-source gate,
  and required point-of-use agent attestation for every restricted form.
- Restricting the agent IABS profile UI to authenticated agent-capable roles.
- Restricting IABS Storage operations to the exact authenticated object path
  `<auth.uid>/iabs.pdf`.

## Verification

- Release preflight passed against `origin/main` with deploy author
  `andrewchri@gmail.com`.
- `tests.test_brokerage_form_source_foundation`: 6 tests passed.
- Restricted-form and brokerage-launch regression tests: 57 tests passed.
- Static gate assertions passed: four restricted-form cards contain the
  aligned role guard, each restricted form requires `formUseAttested`, and the
  server calls `_require_brokerage_txr_authorization` before saving a draft.
- `git diff --check` passed.
- The live Supabase Storage policy verification confirmed exact-path
  select/insert/update/delete policies for the IABS object.

## Release decision

Ready to bundle into the next intentional production deployment. This is not
itself a deployment record; no Vercel deployment was triggered for this batch.

## Rollback

Rollback is the prior Ready production deployment. Do not delete IABS objects,
brokerage memberships, source approvals, or signing records as part of a code
rollback.
