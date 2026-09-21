# OnDemand sign-in clarity and private attribution — September 21, 2026

## Outcome

The first OnDemand enrollment button now says exactly what the click does:
`Email my secure sign-in link`. The prior `Start my 60-day free trial` label
implied that the trial began on the first click even though the click only
sends a passwordless sign-in email. The enrollment card still explains that
the trial begins through secure checkout after the agent opens the link and
confirms a card.

Unlabeled OnDemand visits now fall into a privacy-safe `direct` or `referral`
channel. Explicit campaign tags continue to win. An external referrer is used
only to choose the aggregate `referral` label; HomeOfferFlow does not send or
store the referrer URL, search term, agent identity, or email address with the
landing event.

## Scope and invariants

- No eligibility rule, trial duration, $29 monthly price, card requirement,
  Stripe route, Supabase authentication, or legal-acceptance behavior changed.
- The magic-link destination and email delivery code are unchanged.
- Existing tagged channels and campaigns are unchanged.
- Automatic Git and preview deployments remain disabled. This change belongs
  in the single coordinated post-reset production release.

## Verification

- Focused OnDemand and PWA tests cover the truthful action label, private
  direct/referral classification, installed-app-only update prompt, and the
  unchanged public PWA contract.
- The enrollment card was visually inspected from a temporary local-only
  server; no production request or Vercel deployment was made.
- The exact local candidate passed all 2,368 repository tests. Protected
  `main` must pass again after merge.
- After production release, verify the canonical button label and compare the
  aggregate direct, referral, email-start, magic-link, checkout-return, and
  first-transaction signals before changing pricing or adding another prompt.
