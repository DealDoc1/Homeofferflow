# OnDemand session-start recovery — 2026-09-21

## Outcome

The OnDemand enrollment page now attaches its authentication listener before it
reads the browser's saved session. If that initial read fails, a later recovered
or refreshed sign-in can still render the agent account, continue invite
acceptance, and reach checkout without another page load.

The page also gives a direct, plain-language recovery choice: request a new
secure link or refresh the page.

## Scope, privacy, and cost

- The 60-day trial, $29 monthly renewal, explicit terms acknowledgement,
  eligibility checks, Stripe checkout, and cancellation rules are unchanged.
- No additional identity or transaction data is stored or measured.
- Existing Supabase authentication is reused. No new function, table, vendor,
  preview deployment, or recurring cost is introduced.

## Verification

- A runtime test forces the initial session read to fail, confirms the auth
  listener remains active, then verifies a recovered signed-in session is
  rendered and the invite path continues.
- 82 focused OnDemand enrollment and brokerage-launch tests pass.
- The complete local regression suite passes: 2,381 tests.
- Production verification remains part of the one coordinated post-reset
  release.
