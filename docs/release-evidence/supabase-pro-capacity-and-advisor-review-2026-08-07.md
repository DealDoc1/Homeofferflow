# Supabase Pro capacity and advisor review — 2026-08-07

## Scope

This evidence records the Supabase plan upgrade and the follow-up health and
advisor review. It does not change packet generation, legal-form sources,
signer plans, or production offer-generation routes.

## Live verification

- Organization: `Real Estate Offer Builder`
- Plan: `pro`
- Project: `HomeOfferFlow` (`acqylchftrjjoablvqyq`)
- Status: `ACTIVE_HEALTHY`
- Database engine: PostgreSQL 17.6
- Region: `us-west-2`

The Pro plan removes the previous Supabase free-tier capacity concern. It does
not change the separate Vercel Hobby deployment-cap policy.

## Advisor decision

The live Supabase advisor still reports informational RLS/no-policy findings on
legacy or server-only tables and GraphQL table-exposure warnings for tables that
the current browser application intentionally reads through authenticated Data
API policies. These are reviewed, not ignored:

- Do not apply a blanket `revoke all ... from authenticated` migration.
- Keep the existing owner/brokerage RLS policies and table grants.
- Continue moving sensitive browser dependencies behind server endpoints one
  table at a time, with a real authenticated regression test before revoking a
  grant.
- Keep the `hof_usage_events` server-only hardening already applied.

## Verification evidence

- Local release preflight passed for the current non-form evidence branch.
- Full regression suite passed: `424 tests`, `OK`.
- The live `hof_standalone_agreements` form-code constraint accepts exactly
  `TXR-1501`, `TXR-1506`, `TXR-1507`, and `TXR-1508`.
- Targeted Stripe lifecycle, OnDemand checkout, brokerage authorization, and
  admin-security tests passed.
- Read-only live endpoint checks passed without creating checkout or payment
  side effects: OnDemand launch metadata returned a 60-day trial and $29
  monthly price, while unauthenticated brokerage-admin access returned HTTP
  401.
- Working tree was clean after verification.
- No Vercel deployment was triggered.

## Remaining release gates

This evidence does not mark the roadmap complete. Remaining gates are:

1. Authenticated brokerage-admin and signed-in usage smoke QA.
2. Authenticated point-of-use QA for TXR-1501, TXR-1506, TXR-1507, and TXR-1508.
3. Completed-signature visual QA for any legal-form workflow.
4. Five anonymized AI calibration reviews.
5. One intentional bundled production deployment after all applicable gates pass.
