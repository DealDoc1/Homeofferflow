# Stripe suspension-reason schema verification — 2026-08-07

## Scope

This evidence records the live, backward-compatible Supabase schema prerequisite
for the pushed Stripe lifecycle guardrail. It does not change subscriptions,
offers, PDFs, or legal-form workflows.

## Live verification

- Project: HomeOfferFlow (`acqylchftrjjoablvqyq`)
- Project status: `ACTIVE_HEALTHY`
- Table: `public.hof_brokerage_members`
- Column: `suspension_reason text`
- Allowed values: `NULL`, `billing`, `manual`
- Partial index: `hof_brokerage_members_suspension_reason_idx`
- Existing rows were not rewritten.

## Code checkpoint

- Branch: `agent/seller-disclosure-workspace-link`
- Commit: `77e787b`
- Automated suite: 474 tests passed.
- Vercel deployment: intentionally not triggered; the change is bundled for the
  next planned release under the Vercel Hobby deployment-cap policy.

## Remaining verification

After the code is deployed, verify that a billing renewal restores only a
`billing` suspension, never a `manual` suspension or removed membership.
