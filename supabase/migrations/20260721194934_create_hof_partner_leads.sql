create table if not exists public.hof_partner_leads (
  id uuid primary key default gen_random_uuid(),
  partner_type text not null default 'other'
    check (partner_type in (
      'title', 'lender', 'inspection', 'home_warranty', 'insurance',
      'photography_video', 'staging', 'repairs_handyman', 'cleaning',
      'moving_storage', 'lawn_pool', 'other'
    )),
  company_name text not null,
  contact_name text not null,
  contact_email text not null,
  contact_phone text,
  website_url text,
  market_area text not null,
  customer_focus text,
  monthly_budget_range text not null default 'discuss'
    check (monthly_budget_range in ('under_250', '250_499', '500_999', '1000_plus', 'discuss')),
  preferred_model text not null default 'founding_pilot'
    check (preferred_model in ('founding_pilot', 'monthly_placement', 'market_exclusive', 'discuss')),
  message text,
  source text not null default 'website_partner_modal',
  utm_source text,
  utm_medium text,
  utm_campaign text,
  utm_content text,
  landing_page text,
  status text not null default 'new'
    check (status in ('new', 'contacted', 'qualified', 'waitlist', 'converted', 'declined')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists hof_partner_leads_status_created_idx
  on public.hof_partner_leads(status, created_at desc);
create index if not exists hof_partner_leads_type_market_idx
  on public.hof_partner_leads(partner_type, market_area);

drop trigger if exists hof_partner_leads_set_updated_at on public.hof_partner_leads;
create trigger hof_partner_leads_set_updated_at
before update on public.hof_partner_leads
for each row execute function private.hof_set_updated_at();

alter table public.hof_partner_leads enable row level security;
revoke all on table public.hof_partner_leads from public, anon, authenticated;
grant select, insert, update, delete on table public.hof_partner_leads to service_role;

drop policy if exists "partner_leads_server_only" on public.hof_partner_leads;
create policy "partner_leads_server_only"
on public.hof_partner_leads
for all
to authenticated
using (false)
with check (false);

comment on table public.hof_partner_leads is
  'Founding partner applications submitted through the server-side HomeOfferFlow partner intake.';

