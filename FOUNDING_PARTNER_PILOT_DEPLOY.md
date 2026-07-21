# HomeOfferFlow Founding Partner Pilot — Deployment Runbook

## Update name

Founding Partner Revenue Pilot v1

## What it adds

- Public founding-partner application modal linked from the site footer.
- Server-side `/api/partner-lead` intake endpoint.
- Supabase `hof_partner_leads` table with server-only access, RLS, and explicit grants.
- UTM/source attribution for founder outreach and social campaigns.
- Founding-partner lead count and lead list in the authenticated admin dashboard.
- Revenue roadmap split between the near-term founding pilot and the later full partner marketplace.

This update does not change the production TREC contract, PDF coordinates, offer-generation routes, pricing, Stripe, or SignWell behavior.

## Deployment order

### 1. Apply the database migration

Run the full contents of:

`supabase/homeofferflow_partner_leads.sql`

in the HomeOfferFlow Supabase SQL editor.

Confirm:

- `public.hof_partner_leads` exists.
- RLS is enabled.
- `anon` and `authenticated` do not have table privileges.
- `service_role` has select, insert, update, and delete privileges.

### 2. Deploy a Vercel preview

Include:

- `api/partner-lead.py`
- `api/admin-dashboard.py`
- `index.html`
- `supabase/homeofferflow_partner_leads.sql`
- `supabase/homeofferflow_product_tracker.sql`
- `supabase/homeofferflow_revenue_priority_2026_07.sql`
- `supabase/README.md`
- `tests/test_partner_lead.py`
- `tests/test_admin_tracker.py`

Do not alter or replace the live PDF-generation files as part of this deployment.

### 3. Preview QA

Open the preview with:

`?partner=1&utm_source=founder_outreach&utm_medium=direct&utm_campaign=founding_partner_pilot`

Verify:

1. The partner modal opens automatically.
2. The pilot disclaimer clearly says there is no promise of referrals, leads, exclusivity, or transaction volume.
3. Missing required fields are rejected.
4. An invalid email is rejected.
5. A valid submission returns the success state.
6. The row appears in `public.hof_partner_leads` with the UTM values.
7. The authenticated admin dashboard shows the new lead.
8. A non-admin cannot load partner-lead data from the admin endpoint.
9. The main buyer-offer flow still opens and the production PDF routes are unchanged.

### 4. Promote after preview approval

Promote the verified Vercel preview to production. Then repeat one valid partner submission using:

`https://www.homeofferflow.com/?partner=1&utm_source=founder_outreach&utm_medium=direct&utm_campaign=founding_partner_pilot`

Delete or mark the production smoke-test lead as `declined` after verification.

## Rollback

If the public intake fails:

1. Roll back the Vercel deployment.
2. Leave `hof_partner_leads` in place so submitted leads are not lost.
3. Do not roll back or modify any offer/PDF route.

