# Stripe lifecycle QA results — isolated branch — 2026-08-10

## Scope

This is the completed, non-production Stripe lifecycle verification for the
isolated Supabase branch `stripe-lifecycle-qa` (`mtalxbxlutkuqcafjsac`) and
the matching Vercel preview deployment. It records only test identifiers and
resulting application states; no keys, webhook payloads, card data, or buyer
data are included.

## Isolation

- QA runtime: non-production Vercel preview, routed to the isolated Supabase
  branch rather than production (`acqylchftrjjoablvqyq`).
- Stripe endpoint: test-mode destination `we_1U2tMDAELe66ESXnPHnly1vU`.
- Endpoint access: Vercel Automation Protection Bypass was used only for this
  isolated QA destination; ordinary protected deployment access remained on.
- Production safety: the full automated suite includes production and
  shared-database rejection coverage; no test event was sent to production.

## Live test evidence

All listed Stripe deliveries returned HTTP 200 from the isolated QA webhook.

| Lifecycle check | Stripe event/action | Persisted QA result |
| --- | --- | --- |
| Card-required trial checkout | Test Checkout, $0 due today | Agent subscription created as `trialing` with a 60-day trial. |
| Checkout and create delivery | `checkout.session.completed`, `customer.subscription.created` | Both ledger records processed. |
| Trial payment | `invoice.payment_succeeded`, `invoice.paid` | Subscription remained `trialing`, not incorrectly promoted to active. |
| Cancel at period end | `customer.subscription.updated` | `cancel_at_period_end=true` was persisted while access remained trialing. |
| Duplicate delivery | Manual resend of the same update event | HTTP 200; the existing ledger event stayed one processed record. |
| Payment failure | Real sandbox declined-card invoice, `invoice.payment_failed` | Subscription became `past_due`. |
| Billing suspension | Fresh `past_due` subscription update with an existing agent seat | Seat became `suspended` with `suspension_reason=billing`. |
| Manual suspension preservation | Successful sandbox invoice recovery | Subscription returned `active`; manually suspended seat stayed `suspended` with `suspension_reason=manual`. |
| Removed-seat preservation | `customer.subscription.deleted` after the seat was marked removed | Seat remained `removed`; webhook did not recreate or reactivate it. |
| Cancellation | `customer.subscription.deleted` | Subscription became `canceled`. |

## Automated regression

`PYTHONPATH=/private/tmp/homeofferflow_test_deps ... python3 -m unittest discover -s tests`
completed successfully: **718 tests passed**.

## Cleanup follow-up

The test endpoint and isolated QA branch remain available only for repeatable
regression coverage. Before the branch is retired, remove the endpoint’s
automation-bypass query value, rotate the bypass secret, and delete the
disposable Stripe test subscriptions and QA auth user.
