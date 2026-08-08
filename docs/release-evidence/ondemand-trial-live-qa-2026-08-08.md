# OnDemand trial launch live QA — 2026-08-08

## Scope

Read-only browser verification of the production OnDemand Realty launch path:

`https://www.homeofferflow.com/ondemand.html`

This check did not submit Stripe Checkout, create a subscription, or charge a
payment method.

## Observed production behavior

- The page identifies the brokerage as **OnDemand Realty**.
- The signed-in account shown during the check was `andrewchri@gmail.com`.
- The plan shows **$0 today** and **60 days free**.
- The page disclosed the calculated renewal date, **October 7, 2026**, and
  **$29/month** automatic renewal unless canceled.
- The page states that a card is required today and that cancellation is
  available before renewal.
- The consent checkbox links to Terms of Service, Privacy Policy, Disclaimer,
  and E-Sign Consent.
- Before consent, `Continue to secure checkout` was disabled.
- After checking the exact billing/renewal consent, the button became enabled.
- The launch copy accurately limits the current product to supported
  purchase-offer packets/addenda and Seller Temporary Residential Lease; it
  explicitly says standalone buyer-representation, listing, and seller
  disclosure signing workflows are not yet live.

## Result

**Pass for launch-page gating and disclosure.** The production path presents
the agreed 60-day card-required trial and $29/month renewal terms, requires
affirmative consent, and does not claim a complete transaction-form library.

Stripe Checkout submission and lifecycle mutation remain covered by the
isolated test-mode lifecycle runbook; no payment test was submitted during this
QA check.
