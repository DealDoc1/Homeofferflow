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
   testing Stripe. Verify that `hof_subscriptions`,
   `hof_stripe_webhook_events`, and the `suspension_reason` column from
   `supabase/homeofferflow_billing_suspension_reason.sql` exist there.
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

Before creating the endpoint, run the repository preflight against the branch
URL. It prints booleans only and fails unless every isolation control is true:

```bash
python scripts/verify_stripe_lifecycle_isolation.py \
  --expected-supabase-url https://<isolated-branch-ref>.supabase.co
```

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

## Brokerage suspension safety

- Stripe billing suspension writes `suspension_reason=billing`.
- A broker-dashboard suspension writes `suspension_reason=manual`.
- A successful Stripe renewal may restore only an existing `billing` suspension;
  it must not undo a broker's manual suspension.
- Billing events must not convert a removed membership into a suspended or active
  seat.

## Evidence and cleanup

- Capture the nonproduction deployment URL, isolated Supabase branch reference,
  Stripe test endpoint ID, event IDs, and resulting status fields.
- Confirm the platform-admin Billing Webhook Activity view shows delivery
  metadata only, never card, customer-email, or full-event data.
- Remove the Stripe test endpoint and test environment variables when lifecycle
  QA is complete.
- Delete or pause the isolated Supabase branch once no longer needed to stop
  its hourly cost.

For each required intermediate state, capture a privacy-limited checkpoint
after the Stripe delivery using the repository helper below. The helper fails
closed unless the runtime is nonproduction and the database URL is the
explicitly isolated test URL.

```bash
python scripts/capture_stripe_lifecycle_snapshot.py \
  --checkpoint "past_due suspension" \
  --output artifacts/stripe-lifecycle/past-due-suspension.json
```

Repeat this for trialing, cancel-at-period-end, recovery, duplicate delivery,
removed/manual membership preservation, and production test-event rejection.
The resulting JSON contains status counts and lifecycle dates only; it is not a
replacement for the signed Stripe delivery itself.

## Automated guard

Run this before the manual checklist:

```bash
python3 \
-m unittest tests.test_subscription_lifecycle_security
```

Run this with the repository's normal test dependencies. Do not prepend the
old `hof_httpx_only` compatibility shim: it intentionally omits
`httpx.Client`, while the lifecycle tests replace that client with deterministic
test doubles.

The suite proves that production rejects Stripe test-mode events, a preview
sharing production Supabase also rejects them, and only an explicitly isolated
nonproduction runtime can accept them.
