# Stripe subscription lifecycle QA

Use this runbook only against an isolated Supabase branch and a nonproduction
Vercel deployment. It exists to prove the subscription lifecycle without ever
sending a Stripe test event to the production database.

## Non-negotiable isolation gate

Before creating a Stripe test webhook endpoint, confirm all of the following:

- The Vercel deployment is a `preview`, `development`, or `test` runtime.
- `SUPABASE_URL` points to the isolated branch database.
- `STRIPE_WEBHOOK_TEST_SUPABASE_URL` equals that exact isolated branch URL.
- `SUPABASE_PRODUCTION_URL` equals the canonical production Supabase URL and
  is different from `SUPABASE_URL`.
- `STRIPE_WEBHOOK_ALLOW_TEST_EVENTS=true`.
- `STRIPE_WEBHOOK_TEST_ENVIRONMENT` exactly matches the nonproduction Vercel
  environment.
- `STRIPE_SUBSCRIPTION_WEBHOOK_SECRET` is the secret for the Stripe **test
  mode** endpoint only.

Do not set these test-event variables on a production Vercel deployment. The
webhook code rejects `livemode=false` events on production even if a flag is
mistakenly present; this runbook is the second safety layer, not a replacement
for that guard.

## Environment preparation

1. Create an isolated Supabase branch. Its database begins without production
   user data.
2. Run the tracked HomeOfferFlow Supabase migrations on that branch before
   testing Stripe. Verify that `hof_subscriptions` and
   `hof_stripe_webhook_events` exist there.
3. Deploy the exact release branch to a nonproduction Vercel URL with the
   branch database credentials and the isolation variables above.
4. In Stripe **test mode**, create a webhook endpoint for:

   ```text
   https://<nonproduction-host>/api/stripe-webhook
   ```

5. Subscribe it to these events:

   ```text
   checkout.session.completed
   customer.subscription.created
   customer.subscription.updated
   customer.subscription.deleted
   invoice.paid
   invoice.payment_succeeded
   invoice.payment_failed
   ```

6. Configure the test checkout/Price IDs only on the nonproduction deployment.
   Do not reuse a live key, live webhook secret, or production Supabase
   service-role key.

## Required lifecycle checks

Use a dedicated test account and Stripe test card. Record Stripe event IDs and
only the resulting lifecycle fields below; do not paste buyer, card, or full
webhook payload data into tickets or the dashboard.

| Step | Stripe test action | Expected HomeOfferFlow result |
|---|---|---|
| 1 | Start Agent checkout with the 60-day trial | Card is collected; $0 is due today; the future $29/month renewal is disclosed. |
| 2 | Complete checkout | A subscription row is created for the test account with `trialing` status and the correct trial end. |
| 3 | Deliver `customer.subscription.created` | The isolated ledger records the event as `processed`; no duplicate membership is created. |
| 4 | Deliver `invoice.paid` during the trial | The subscription remains `trialing`, not incorrectly promoted to `active`. |
| 5 | Cancel at period end through Stripe test mode | `cancel_at_period_end=true` is recorded; access persists through the stored end date. |
| 6 | Restore the subscription or create another test subscription, then deliver `invoice.payment_failed` | Subscription becomes `past_due`; an existing agent brokerage membership becomes `suspended`; no unrelated account is affected. |
| 7 | Deliver `customer.subscription.deleted` | Subscription becomes `canceled`; an existing agent brokerage membership becomes `suspended`; brokerage activation is not re-created. |
| 8 | Resend a previously processed Stripe event | Endpoint returns success without reapplying the billing mutation; its ledger row remains a single event record. |
| 9 | Send one Stripe test event to the production endpoint only if Stripe allows a safe manual delivery | Production returns a rejection for `livemode=false`; do not repeat or use a live event. |

## Evidence and cleanup

- Capture the nonproduction deployment URL, isolated Supabase branch reference,
  Stripe test endpoint ID, event IDs, and resulting status fields.
- Confirm the platform-admin Billing Webhook Activity view shows delivery
  metadata only, never card, customer-email, or full-event data.
- Remove the Stripe test endpoint and test environment variables when lifecycle
  QA is complete.
- Delete or pause the isolated Supabase branch once no longer needed to stop
  its hourly cost.

## Automated guard

Run this before the manual checklist:

```bash
PYTHONPATH=/private/tmp/hof_httpx_only \
/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
-m unittest tests.test_subscription_lifecycle_security
```

The suite proves that production rejects Stripe test-mode events, a preview
sharing production Supabase also rejects them, and only an explicitly isolated
nonproduction runtime can accept them.
