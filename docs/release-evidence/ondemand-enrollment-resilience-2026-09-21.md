# OnDemand enrollment resilience — September 21, 2026

## Outcome

The OnDemand passwordless sign-in path and anonymous landing measurement no
longer wait for optional brokerage configuration and styling to load. An agent
can immediately enter an email and request the secure sign-in link while the
page refreshes the brokerage name, logo, and color in the background.

If that optional request fails, the page explains that the secure sign-in link
is still available and that final enrollment terms are confirmed before
checkout. The notice uses a neutral treatment instead of presenting a false
blocking error. A later sign-in or checkout result is not overwritten by a
late configuration warning.

## Authority and safety boundary

- The server remains authoritative for OnDemand eligibility, brokerage
  membership, trial terms, and Stripe checkout.
- No trial duration, $29 monthly price, card requirement, cancellation copy,
  magic-link destination, invitation rule, legal acceptance, or checkout route
  changed.
- No identity, email address, referrer URL, or free-form data was added to
  analytics.
- Automatic Git and preview deployments remain disabled. This change belongs
  in the single coordinated post-reset production release.

## Verification

- Focused enrollment, brokerage-launch, script-syntax, legal-acceptance, and
  PWA tests cover the nonblocking sequence and unchanged safety contracts.
- The exact local candidate passed all 2,369 repository tests. Protected
  `main` must pass again after merge.
- Production verification must confirm that an ordinary OnDemand visit shows
  the enrollment card immediately and that a simulated configuration failure
  leaves the secure-link request usable before this item is marked verified.
