# Public OnDemand launch-scope live review — 2026-08-07

## Scope

This was a read-only inspection of the public `/ondemand` launch page. It did
not send a sign-in link, create a subscription, change brokerage data, or
activate a restricted form workflow.

## Verified live copy

- OnDemand Realty is identified as the brokerage launch.
- The plan shows `$0 today`, a 60-day free period, renewal at `$29/month`,
  and `Cancel anytime`.
- The page describes the currently supported purchase-offer packet, supported
  purchase addenda, Seller Temporary Residential Lease when applicable,
  buyer electronic-signature delivery, and the connected agent account.
- The page expressly states that standalone buyer-representation agreements,
  listing agreements, and seller-disclosure notices are not yet created or
  sent by HomeOfferFlow.
- The page explains that broader form coverage will be staged behind source,
  signer, visual-QA, and transaction safeguards.

## Gate status

The public launch copy is aligned with the current roadmap and does not claim a
complete agent transaction-form library. Authenticated account, billing,
brokerage-admin, and restricted-form QA remain separate gates.

## Read-only endpoint checks

- `GET /api/create-subscription-checkout?launch=ondemand` returned HTTP 200 with
  `trialDays: 60`, `monthlyPrice: 29`, and the active `ondemand` brokerage.
- `GET /api/admin-dashboard?scope=brokerage` without a session returned HTTP
  401 with `A valid signed-in session is required.`
- No checkout session was created and no payment method or email was submitted.
