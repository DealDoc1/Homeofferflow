-- A public partner placement must be traceable to a paid application and an
-- explicit platform-admin confirmation that the required advertising agreement
-- is on file. This does not alter Stripe subscriptions or existing placements.

begin;

alter table public.hof_partner_placements
  add column if not exists source_lead_id uuid,
  add column if not exists agreement_confirmed_at timestamptz,
  add column if not exists activated_at timestamptz;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'hof_partner_placements_source_lead_id_fkey'
      and conrelid = 'public.hof_partner_placements'::regclass
  ) then
    alter table public.hof_partner_placements
      add constraint hof_partner_placements_source_lead_id_fkey
      foreign key (source_lead_id)
      references public.hof_partner_leads(id)
      on delete restrict;
  end if;
end $$;

create unique index if not exists hof_partner_placements_active_source_lead_key
  on public.hof_partner_placements(source_lead_id)
  where source_lead_id is not null and is_active is true;

create index if not exists hof_partner_placements_source_lead_id_idx
  on public.hof_partner_placements(source_lead_id);

comment on column public.hof_partner_placements.source_lead_id is
  'The paid founding-partner application that authorized this platform placement.';
comment on column public.hof_partner_placements.agreement_confirmed_at is
  'Server-recorded time a platform administrator confirmed the required advertising agreement was on file.';
comment on column public.hof_partner_placements.activated_at is
  'Server-recorded time the paid, agreement-confirmed placement became active.';

commit;
