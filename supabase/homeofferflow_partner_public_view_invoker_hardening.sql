-- Harden the legacy public placement view. The live partner directory is served
-- by the validated API endpoint; it does not query this view. Keeping an
-- anonymous SECURITY DEFINER view would bypass the base table's RLS boundary.

begin;

create or replace view public.hof_public_partner_placements
with (security_invoker = true)
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
grant select on table public.hof_public_partner_placements to service_role;

comment on view public.hof_public_partner_placements is
  'Server-only curated partner-placement view. The public directory is served by the validated API; no anonymous database view access is permitted.';

commit;
