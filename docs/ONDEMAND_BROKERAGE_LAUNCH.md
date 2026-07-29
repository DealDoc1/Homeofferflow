# HomeOfferFlow — OnDemand Realty Brokerage Launch

## 1. Update name

**OnDemand Realty Brokerage Launch — 60-Day Agent Trial**

## 2. What it does

- Adds a clean `/ondemand` launch route.
- Requires agents to sign in with a verified Supabase account before checkout.
- Uses the existing `STRIPE_AGENT_MONTHLY_PRICE_ID`; it does not create a
  duplicate Stripe Product or Price.
- Creates a native Stripe subscription trial:
  - $0 today
  - card required at checkout
  - 60 days free
  - $29/month after the trial
  - automatic monthly renewal unless canceled
- Disables promotion codes on the OnDemand path while preserving promotion
  codes and monthly/annual choices on the standard Agent and Investor paths.
- Associates successful OnDemand enrollees with the OnDemand Realty brokerage.
- Configures confirmed broker Tyler Demando through
  `ONDEMAND_BROKER_EMAIL=tyler@ondemanddfw.com`. No license, logo, address, or
  phone was invented.
- Adds broker-level activity reporting with no buyer names, buyer emails,
  property addresses, offer terms, prices, or PDF/document contents.
- Discloses on `/ondemand` that this launch covers the current buyer-side offer
  packet and supported purchase addenda only. Standalone buyer representation
  agreements, listing agreements, and seller disclosure notices remain in the
  brokerage's approved workflow until their dedicated releases are complete.
- Moves account role, brokerage membership, and subscription authority to
  server-controlled data.
- Does not edit `api/fill-pdf.py`, `20-18_0.pdf`, the staging coordinate file,
  or the offer-generation/signing workflow.

## 3. Files

- `ondemand.html`
- `vercel.json`
- `index.html`
- `api/create-subscription-checkout/index.py`
- `api/stripe-webhook/index.py`
- `api/admin-dashboard.py`
- `supabase/homeofferflow_ondemand_brokerage_launch.sql`
- `supabase/homeofferflow_ondemand_broker_seed.sql`
- `supabase/homeofferflow_brokerage_security_hardening.sql`
- `tests/test_ondemand_brokerage_launch.py`
- `docs/AGENT_FORM_COVERAGE_ROADMAP.md`

## 4. Environment and account setup

### Existing environment variables that must remain configured

- `STRIPE_SECRET_KEY`
- `STRIPE_AGENT_MONTHLY_PRICE_ID`
- `STRIPE_AGENT_ANNUAL_PRICE_ID`
- `STRIPE_INVESTOR_MONTHLY_PRICE_ID`
- `STRIPE_INVESTOR_ANNUAL_PRICE_ID`
- `STRIPE_SUBSCRIPTION_WEBHOOK_SECRET`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (or an already-supported alias)
- `RESEND_API_KEY` for broker-created invitation email delivery

The OnDemand trial reuses `STRIPE_AGENT_MONTHLY_PRICE_ID`. The project owner
confirmed on July 27, 2026 that this Price is recurring monthly at **$29 USD**.

### New required environment variable

Set this to the broker's exact, confirmed Supabase sign-in email:

```text
ONDEMAND_BROKER_EMAIL=tyler@ondemanddfw.com
```

Apply it to Preview and Production. Do not guess this value. An exact email
match is what gives the account `brokerage_admin` / `broker_admin` authority.
All other OnDemand users are enrolled as agents.

### Brokerage invitation email delivery

When a brokerage administrator creates or resends an agent invite, HomeOfferFlow
emails the secure, email-bound invite link through Resend. The invite record is
created before delivery is attempted, so a temporary email-provider failure does
not lose the invite: the broker still receives a copied link to send manually.

The existing `RESEND_API_KEY` is sufficient. Optionally configure:

```text
BROKERAGE_INVITE_FROM_EMAIL=offers@homeofferflow.com
BROKERAGE_INVITE_REPLY_TO=support@homeofferflow.com
```

If the optional values are absent, the application uses the existing feedback
sender address and then the established HomeOfferFlow sender fallback.

### Supabase Auth redirect allowlist

Add:

```text
https://www.homeofferflow.com/ondemand
https://homeofferflow.com/ondemand
```

Add the exact Vercel Preview URL used for QA as well. Keep existing HomeOfferFlow
redirect URLs.

### Stripe webhook events

Confirm the existing subscription webhook sends these events to the deployed
`/api/stripe-webhook` endpoint:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`

## 5. Database deployment

The additive launch migration was applied to Supabase on July 27, 2026:

```text
supabase/homeofferflow_ondemand_brokerage_launch.sql
```

It created/updated:

- the `OnDemand Realty` brokerage row with slug `ondemand`
- trial and brokerage attribution columns on `hof_subscriptions`
- the database-level `brokerage_admin` profile role
- membership uniqueness and role/status constraints

The brokerage contact is Tyler Demando (`tyler@ondemanddfw.com`), as confirmed
by the project owner. His exact Supabase sign-in email becomes authoritative
only when the Vercel environment variable is configured.

Apply this idempotent broker seed after Tyler's Supabase Auth account exists:

```text
supabase/homeofferflow_ondemand_broker_seed.sql
```

It assigns Tyler the `brokerage_admin` profile role and active `broker_admin`
membership for OnDemand Realty without creating or guessing any personal data.

Apply this migration in the coordinated application release:

```text
supabase/homeofferflow_brokerage_security_hardening.sql
```

That second migration removes browser permissions that previously allowed
users to create subscription state, brokerage membership, or authorization
fields themselves. Apply it immediately with the updated `index.html`; the old
browser code should not be left running after those permissions are removed.

## 6. Production QA

This project deliberately uses **one intentional Production deployment** after
tests pass. Do not create routine Vercel previews; the Hobby deployment limit
requires release batching.

1. Confirm `ONDEMAND_BROKER_EMAIL=tyler@ondemanddfw.com` and the required
   Stripe/Supabase/Resend environment variables are present in Production.
2. Open `/ondemand` in a private browser window.
5. Verify the page says:
   - `$0 today`
   - `60 days free`
   - `Then $29/month beginning [displayed date]`
   - `Cancel anytime`
6. Request a magic link with an agent test email.
7. Return to `/ondemand`; confirm the verified email is displayed.
8. Confirm checkout stays disabled until the renewal checkbox is checked.
9. Continue to Stripe.
10. In Stripe test mode, use `4242 4242 4242 4242`, any future expiration,
    and any CVC.
11. Confirm Stripe requires the card and shows a $0 trial with the next charge
    at $29 after 60 days.
12. Complete checkout and verify the return message.
13. In Supabase verify:
    - `hof_profiles.brokerage_id` points to the OnDemand brokerage
    - the agent profile role remains `agent`
    - `hof_brokerage_members.status` becomes `active` after the webhook
    - `hof_subscriptions.status` is `trialing`
    - `trial_ends_at` is populated
    - `launch_source` is `ondemand`
14. Sign in using the configured broker email:
    - profile role must be `brokerage_admin`
    - membership role must be `broker_admin`
    - Brokerage tab must show agents and aggregate activity
    - it must not show buyer, property, price, terms, payload, or document data
15. Revisit `/ondemand` with the active test account and confirm a duplicate
    checkout is rejected.
16. Test the standard Agent monthly/annual and Investor monthly/annual buttons.
    They must still create their normal checkout sessions and may still accept
    promotion codes.
17. Test the Stripe billing portal and cancellation behavior.

## 7. Production deployment

1. Confirm the production QA checklist passes on the completed release.
2. Immediately apply
   `supabase/homeofferflow_brokerage_security_hardening.sql`.
3. Open `https://www.homeofferflow.com/ondemand`.
4. Repeat one agent test and one configured broker test.
5. Verify Stripe webhook delivery and Supabase row state.
6. Verify these existing production paths:
   - home page loads
   - Agent and Investor authentication
   - existing paid subscriber billing portal
   - normal subscription checkout
   - offer dashboard
   - offer generation
   - SignWell signature flow
7. Run the repository test suite:

```text
PYTHONPATH=/private/tmp/homeofferflow_test_deps \
PYTHONPYCACHEPREFIX=/private/tmp/hof_pycache \
/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
-m unittest discover -s tests
```

## 8. Rollback

- Roll back the Vercel deployment if the launch page or checkout fails.
- The additive launch migration can remain; it does not alter offer/PDF behavior.
- Set `hof_brokerages.is_active = false` for slug `ondemand` to stop new launch
  enrollment without deleting history.
- Do not restore browser-side role or subscription write access as a normal
  rollback. Fix forward or temporarily disable `/ondemand`.
- Production `api/fill-pdf.py` and `20-18_0.pdf` were not changed by this release.
