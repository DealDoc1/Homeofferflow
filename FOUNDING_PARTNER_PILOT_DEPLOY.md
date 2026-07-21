# HomeOfferFlow Founding Partner Pilot — Deployment Runbook

## Update name

Founding Partner Revenue Pilot v2

## What it adds

- Three selectable monthly advertising tiers priced per category and market:
  - Market Listing — $149
  - Featured Partner — $399
  - Premier Market Sponsor — $799
- An exact placement comparison covering category pages, provider selection, buyer workflow, agent/FSBO workflow, and reporting.
- Premier sponsored inventory above the neutral category directory and inside relevant workflow moments.
- Neutral provider results for every tier: paid partners are never preselected, required, or ranked inside the selector because of payment.
- Public tier selection stored through the existing `/api/fsbo-lead` partner-intake path.
- UTM/source attribution and authenticated admin review.

This release changes partner-pilot presentation only. It does not change TREC contract files, PDF coordinates, offer-generation routes, Stripe, or SignWell.

## Commercial rules carried by the preview

1. Rates are monthly and apply to one category in one market.
2. All paid advertising modules are labeled `Sponsored`.
3. Premier inventory is limited to one active sponsored position per category and market during the pilot.
4. The neutral provider selector never preselects a paid partner and does not rank providers based on payment.
5. A user may choose any provider or no provider.
6. Fees are not contingent on referrals, leads, transactions, or closings.
7. Final availability and deliverables require a written advertising agreement.

The commercial agreement and final implementation should receive legal/compliance review before paid settlement-service advertising is activated.

## Preview files

- `index.html`
- `api/fsbo-lead.py`
- `api/admin-dashboard.py`
- `tests/test_partner_lead.py`
- `tests/test_partner_tier_ui.py`
- `supabase/homeofferflow_partner_leads.sql`
- `supabase/homeofferflow_product_tracker.sql`
- `PARTNER_RATE_CARD.md`

## Preview QA

Open the existing preview with:

`?partner=1&utm_source=founder_outreach&utm_medium=direct&utm_campaign=founding_partner_pilot`

Verify:

1. The partner modal opens automatically.
2. The three tier cards show $149, $399, and $799 monthly rates per category and market.
3. Featured Partner is selected by default.
4. Selecting each card updates the selected-tier summary, budget band, and submit-button copy.
5. The placement table clearly distinguishes sponsored inventory from neutral provider selection.
6. The consumer-choice disclosure says users may choose any provider or none.
7. Missing required fields and invalid email addresses are rejected.
8. A valid submission returns the success state.
9. The stored row has the selected `preferred_model`, matching budget band, and UTM values.
10. The authenticated admin dashboard shows the submitted lead.
11. The main buyer-offer flow still opens and no PDF-generation file changed.

Delete the preview smoke-test lead after verification.

## Production gate

Do not promote this partner preview to production until:

- the user approves the tier names, rates, and visual presentation;
- the provider-selection separation is verified in the rendered preview;
- the partner advertising agreement is reviewed;
- one complete test lead has been stored and deleted successfully.

## Rollback

If the public intake or presentation fails:

1. Roll back the Vercel preview deployment.
2. Leave `hof_partner_leads` in place so submitted leads are not lost.
3. Do not roll back or modify any offer/PDF route.
