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

Released in the intentional production deployment below after the preflight
and regression checks passed.

## Production deployment record

- Vercel deployment: `dpl_7qEbd31vKKtikB9N9kZb9nvqHoKb`
- Production commit: `a3cb94b23640b66a70a9c6bf52d834f040d34eb6`
- Branch: `release/intentional-prod-2026-07-31-ai-scenario-gate`
- State: `READY`
- Canonical aliases verified: `https://homeofferflow.com` and
  `https://www.homeofferflow.com`
- Live OnDemand launch verification: `https://www.homeofferflow.com/ondemand`
  returned HTTP 200 and showed the brokerage launch, 60-day trial, $29/month
  renewal disclosure, current workflow scope, and Texas REALTORS®/NAR
  restricted-form authorization language.
- Live launch configuration verification: `GET /api/create-subscription-checkout?launch=ondemand`
  returned `trialDays=60`, `monthlyPrice=29`, and the OnDemand Realty brokerage
  record.
- Post-release focused regression run: 79 tests passed, including brokerage
  gate/source foundation, standalone-agreement validation, OnDemand checkout,
  seller temporary lease reconciliation, TXR tracker reconciliation, mobile
  roadmap, and release-preflight coverage.

## Rollback

Rollback is the prior Ready production deployment. Do not delete IABS objects,
brokerage memberships, source approvals, or signing records as part of a code
rollback.
