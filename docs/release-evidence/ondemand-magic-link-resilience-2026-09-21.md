# OnDemand secure-link recovery — 2026-09-21

## Outcome

The OnDemand enrollment card now recovers when the passwordless sign-in request
is rejected by the browser or network before Supabase can return a normal
authentication response. The button is restored to **Email my secure sign-in
link** and the existing customer-safe retry message is shown.

This closes a conversion failure where a prospective agent could otherwise be
left with a permanently disabled **Sending…** button and no next step.

## Evidence basis

- The 30-day aggregate baseline recorded 17 OnDemand landing views, one trial
  entry selection, and no checkout start. The sample is small and may contain
  internal QA, so it supports removing known friction rather than a pricing or
  acquisition conclusion.
- Source inspection confirmed that a returned authentication error restored the
  button, while a rejected `signInWithOtp` promise bypassed all recovery logic.

## Scope, privacy, and cost

- The plan, 60-day trial, $29 monthly renewal, card requirement, legal
  acknowledgement, server-side eligibility, and Stripe checkout are unchanged.
- No email, account, client, property, document, or device data is added to
  analytics.
- No new service, function, table, provider, or recurring cost is introduced.

## Verification

- 78 focused OnDemand enrollment and brokerage-launch tests pass, including the
  actual inline-script syntax check.
- The complete local regression suite passes: 2,377 tests.
- Production verification remains part of the one coordinated post-reset
  release; no preview deployment was created.
