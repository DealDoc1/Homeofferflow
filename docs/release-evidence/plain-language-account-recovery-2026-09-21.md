# Plain-language account recovery — 2026-09-21

## User problem

The shared account dialog still used the unexplained term `magic link`, could
show raw authentication-provider errors, and named Supabase in customer-facing
profile and feedback messages. Those details do not help an agent, broker, or
investor complete the next action and could make a routine connection problem
look like a platform configuration failure.

## Candidate change

- Label the primary account action `Email My Secure Sign-In Link` and confirm
  success with the same plain-language term.
- Keep provider diagnostics in the browser console while showing a concise
  retry-and-support path to the customer.
- Replace provider-specific profile connection copy with a clear refresh
  instruction and preserve the user's visible entries after a failed save.
- Confirm feedback is saved securely without naming the database or appending
  raw error text to the customer message.
- Leave authentication, account roles, offer data, analytics event names, and
  provider behavior unchanged.

## Verification

- 70 focused account, landing, profile, feedback, and modal tests passed.
- Full repository suite: 2,389 tests passed in 78.118 seconds.
- A headless Chrome check at a 390 by 844 mobile viewport opened the actual
  account dialog, confirmed the email field received focus, confirmed the
  dialog remained accessibility-visible, and found no `Supabase`, `Auth URL`,
  or `magic link` text in the rendered dialog.
- The local static server intentionally lacks the Vercel Analytics endpoint;
  that expected local-only 404 was not an application error overlay and does
  not affect the verified dialog behavior.

## Release status

Implemented, locally tested, and browser-verified. This change is not
production-live until the single coordinated post-reset deployment completes
and the canonical account dialog is checked again.
