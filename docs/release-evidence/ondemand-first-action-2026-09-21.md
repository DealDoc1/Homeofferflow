# OnDemand first-action placement — 2026-09-21

## Outcome

The OnDemand trial page now places the agent email field and secure-link button
directly beneath the visible $0-today, 60-day-free, and $29-monthly renewal
terms. The enrollment explanation remains available under a concise “What
happens next?” disclosure instead of pushing the first signup action below the
initial screen.

After sign-in, the pre-sign-in explanation is hidden so the agent sees only the
trial acknowledgment and secure-checkout action relevant to the next step.

## Scope, privacy, and cost

- Trial length, price, card requirement, renewal date, cancellation terms,
  eligibility enforcement, passwordless authentication, and Stripe checkout
  are unchanged.
- Existing aggregate funnel measurements remain unchanged, allowing the
  email-start rate to be compared after production release.
- No personal information, database object, vendor, preview deployment, or
  recurring cost is added.

## Verification

- Local browser QA confirmed the email field and secure-link action are visible
  in the initial desktop enrollment view with the price and trial terms.
- Accessibility-tree QA confirmed the three enrollment steps remain available
  from the collapsed “What happens next?” control.
- 83 focused OnDemand launch, funnel, and script tests pass.
- The complete local regression suite passes: 2,385 tests.
- Production conversion comparison remains part of the coordinated post-reset
  release and subsequent aggregate reporting.
