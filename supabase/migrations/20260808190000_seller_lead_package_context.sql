-- Preserve the structured seller-package context collected by the public FSBO intake.
-- The API remains the write boundary for public leads; these columns make the
-- package and routing intent available to authorized follow-up workflows.

begin;

alter table public.hof_seller_leads
  add column if not exists property_city text,
  add column if not exists property_county text,
  add column if not exists property_state text,
  add column if not exists property_zip text,
  add column if not exists service_level text,
  add column if not exists package_name text,
  add column if not exists package_price text,
  add column if not exists timeline text,
  add column if not exists partner_categories jsonb not null default '[]'::jsonb;

alter table public.hof_seller_leads
  add constraint hof_seller_leads_service_level_length
    check (service_level is null or char_length(service_level) <= 80),
  add constraint hof_seller_leads_package_name_length
    check (package_name is null or char_length(package_name) <= 180),
  add constraint hof_seller_leads_timeline_length
    check (timeline is null or char_length(timeline) <= 80),
  add constraint hof_seller_leads_partner_categories_array
    check (jsonb_typeof(partner_categories) = 'array');

commit;
