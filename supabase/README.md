# HomeOfferFlow product tracker

Supabase is the authoritative source for the HomeOfferFlow enhancement roadmap,
QA coverage, field-level results, and release gates.

## Tables

- `hof_roadmap_items`: requested enhancements, status, known issues, and next action.
- `hof_qa_scenarios`: golden packets and targeted form/financing scenarios.
- `hof_qa_runs`: execution history and PDF evidence references.
- `hof_qa_results`: page/section/field results, including coordinate locks.
- `hof_releases`: staging and production release gates.
- `hof_platform_admins`: users allowed to administer the tracker.

## Security

The tracker tables have RLS enabled and no `anon` or `authenticated` table
privileges. The browser does not query them directly. The validated
`/api/admin-dashboard` endpoint verifies the Supabase access token, confirms
platform-admin access, and reads the tracker using the server-only service key.

## SQL files

- `homeofferflow_product_tracker.sql` creates and seeds the current tracker.
- `homeofferflow_tracker_server_access.sql` records the server-only access
  hardening applied after the initial live migration.
- `homeofferflow_ai_feedback_rls_hardening.sql` restricts AI-review snapshots
  and feedback to authenticated owner-scoped reads/inserts; feedback submitted
  through the server route continues to use the service role.
- `homeofferflow_revenue_priority_2026_07.sql` orders the roadmap using market
  adoption, ease of shipping/adoption, and proximity to recurring revenue.
  Current product price has zero weight. Completed production features are in
  the `maintenance` tier so they do not crowd the active work queue.
- `homeofferflow_partner_leads.sql` creates the server-only founding-partner
  application table. The public browser posts to `/api/partner-lead`; only the
  Vercel function and authenticated admin endpoint use the service role.

## Isolated branch preflight

Before creating a paid Supabase development branch, run the local read-only
check:

```bash
python scripts/preflight_supabase_branch.py
```

The repository currently contains deployment SQL artifacts but not a complete
ordered `supabase/migrations/` chain or `supabase/config.toml`, so the check is
expected to fail closed. Do not create a Stripe test branch until the
authoritative migration chain and project configuration are restored.

## Founding partner pilot

The pilot is intentionally separate from the full partner marketplace. It can
collect and qualify title, lender, inspection, warranty, insurance, and seller-
service interest before HomeOfferFlow has enough transaction volume to sell a
durable marketplace or promise category exclusivity. The public deep link is:

`https://www.homeofferflow.com/?partner=1&utm_source=founder_outreach&utm_medium=direct&utm_campaign=founding_partner_pilot`

Apply `homeofferflow_partner_leads.sql` before deploying the public form. The
admin API treats the new dataset as optional so the existing dashboard does not
fail during a staged rollout.
