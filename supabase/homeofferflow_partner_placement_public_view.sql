-- Keep partner contact and agreement records server-only. The public directory
-- receives only the curated fields required to show an active placement.

begin;

revoke all on table public.hof_partner_placements from anon, authenticated;
grant all on table public.hof_partner_placements to service_role;

create or replace view public.hof_public_partner_placements
with (security_invoker = false)
as
select
  id,
  partner_type,
  partner_name,
  website_url,
  logo_url,
  market_area,
  placement_tier,
  monthly_fee,
  created_at
from public.hof_partner_placements
where is_active is true
  and brokerage_id is null;

revoke all on table public.hof_public_partner_placements from public, anon, authenticated;
grant select on table public.hof_public_partner_placements to anon, authenticated;

comment on view public.hof_public_partner_placements is
  'Public partner directory fields only. Contact details, source application IDs, agreement confirmations, and activation timestamps remain server-only.';

commit;
