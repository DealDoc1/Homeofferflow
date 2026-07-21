# HomeOfferFlow Founding Partner Pilot — Deployment Runbook

## Update name

Founding Partner Revenue Pilot v3 — 90-Day Launch Offer

## What it adds

- A 90-day Founding Partner launch offer priced per category and market:
  - Market Listing — $149 one time for the first 90 days; $149/month only if renewed
  - Featured Partner — $399 one time for the first 90 days; $399/month only if renewed
  - Premier Market Sponsor — $799 one time for the first 90 days; $799/month only if renewed
- No setup fee, no automatic renewal, and availability limited to the first 10 approved partners.
- An exact placement comparison covering category pages, provider selection, buyer workflow, agent/FSBO workflow, and reporting.
- Premier sponsored inventory above the neutral category directory and inside relevant workflow moments.
- Neutral provider results for every tier: paid partners are never preselected, required, or ranked inside the selector because of payment.
- Public tier selection stored through the existing `/api/fsbo-lead` partner-intake path.
- UTM/source attribution and authenticated admin review.

This release changes partner-pilot presentation only. It does not change TREC contract files, PDF coordinates, offer-generation routes, Stripe, or SignWell.

## Commercial rules carried by the preview

1. The launch price covers the first 90 days for one category in one market and begins when placement goes live.
2. The pilot has no setup fee and does not renew automatically.
3. A standard monthly rate applies only after a separate written renewal.
4. All paid advertising modules are labeled `Sponsored`.
5. Premier inventory is limited to one active sponsored position per category and market during the pilot.
6. The neutral provider selector never preselects a paid partner and does not rank providers based on payment.
7. A user may choose any provider or no provider.
8. Fees are not contingent on referrals, leads, transactions, or closings.
9. Final availability and deliverables require a written advertising agreement.

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
2. The three tier cards show $149, $399, and $799 as one-time 90-day launch prices, with standard monthly renewal rates visible.
3. Featured Partner is selected by default.
4. Selecting each card updates the 90-day selected-tier summary, expected post-pilot budget band, and submit-button copy.
5. The launch terms clearly state first 10 approved partners, no setup fee, and no automatic renewal.
6. The placement table clearly distinguishes sponsored inventory from neutral provider selection.
7. The consumer-choice disclosure says users may choose any provider or none.
8. Missing required fields and invalid email addresses are rejected.
9. A valid submission returns the success state.
10. The stored row has the selected `preferred_model`, matching budget band, and UTM values.
11. The authenticated admin dashboard shows the submitted lead.
12. The main buyer-offer flow still opens and no PDF-generation file changed.

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
