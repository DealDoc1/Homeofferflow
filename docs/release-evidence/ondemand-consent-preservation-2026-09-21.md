# OnDemand consent preservation — 2026-09-21

## Outcome

The OnDemand enrollment card now preserves an agent's checked trial terms when
Supabase refreshes the session token for that same account. Consent is still
cleared when the signed-in identity changes, so one person's acknowledgement
can never carry into another account.

This removes a quiet checkout interruption where a background token refresh
could uncheck the terms and disable **Continue to secure checkout** while the
agent was completing enrollment.

## Scope, privacy, and cost

- The legal acknowledgement remains explicit and required before checkout.
- The 60-day trial, $29 monthly renewal, card requirement, eligibility checks,
  Stripe flow, and cancellation terms are unchanged.
- No consent is persisted outside the visible page state, and no new analytics,
  identity data, vendor, function, database table, or recurring cost is added.

## Verification

- A runtime test exercises initial sign-in, same-account token refresh, and an
  account switch against the actual enrollment function.
- 80 focused OnDemand enrollment and brokerage-launch tests pass.
- The complete local regression suite passes: 2,379 tests.
- Production verification remains part of the one coordinated post-reset
  release; no preview deployment was created.
