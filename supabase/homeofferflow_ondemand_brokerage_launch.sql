-- HomeOfferFlow OnDemand Realty brokerage launch
-- Apply before deploying the /ondemand launch page and checkout changes.
-- This migration is backward-compatible with existing offer/PDF generation.

begin;

-- Authoritative account roles belong in the database, not user-editable
-- Supabase Auth user_metadata.
alter table public.hof_profiles
  alter column role set default 'agent';

alter table public.hof_profiles
  drop constraint if exists hof_profiles_role_check;

alter table public.hof_profiles
  add constraint hof_profiles_role_check
  check (role in ('agent', 'investor', 'brokerage_admin'));

-- Subscription launch attribution and native Stripe trial dates.
alter table public.hof_subscriptions
  add column if not exists brokerage_id uuid references public.hof_brokerages(id) on delete set null,
  add column if not exists launch_source text,
  add column if not exists trial_started_at timestamptz,
  add column if not exists trial_ends_at timestamptz;

create index if not exists hof_subscriptions_brokerage_id_idx
  on public.hof_subscriptions (brokerage_id);

create index if not exists hof_profiles_brokerage_id_idx
  on public.hof_profiles (brokerage_id);

create index if not exists hof_offers_user_id_created_at_idx
  on public.hof_offers (user_id, created_at desc);

-- A launch slug is the server-side routing key. Broker identity is not seeded;
-- configure ONDEMAND_BROKER_EMAIL in Vercel after the broker confirms the email
-- they will use to sign in.
create unique index if not exists hof_brokerages_slug_unique_idx
  on public.hof_brokerages (lower(slug))
  where slug is not null;

insert into public.hof_brokerages (
  name,
  dba_name,
  slug,
  org_type,
  user_cap,
  billing_status,
  plan_name,
  is_active,
  updated_at
)
select
  'OnDemand Realty',
  'OnDemand Realty',
  'ondemand',
  'brokerage',
  300,
  'trial',
  'OnDemand Agent Launch',
  true,
  now()
where not exists (
  select 1
  from public.hof_brokerages
  where lower(slug) = 'ondemand'
);

update public.hof_brokerages
set
  name = 'OnDemand Realty',
  dba_name = 'OnDemand Realty',
  org_type = 'brokerage',
  user_cap = greatest(coalesce(user_cap, 0), 300),
  plan_name = 'OnDemand Agent Launch',
  is_active = true,
  updated_at = now()
where lower(slug) = 'ondemand';

-- One membership per user per brokerage lets Stripe/webhooks upsert safely.
alter table public.hof_brokerage_members
  alter column brokerage_id set not null,
  alter column user_id set not null;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.hof_brokerage_members'::regclass
      and contype = 'u'
      and pg_get_constraintdef(oid) = 'UNIQUE (brokerage_id, user_id)'
  ) then
    alter table public.hof_brokerage_members
      add constraint hof_brokerage_members_brokerage_user_key
      unique (brokerage_id, user_id);
  end if;
end
$$;

alter table public.hof_brokerage_members
  drop constraint if exists hof_brokerage_members_role_check;

alter table public.hof_brokerage_members
  add constraint hof_brokerage_members_role_check
  check (role in ('agent', 'broker_admin', 'owner'));

alter table public.hof_brokerage_members
  drop constraint if exists hof_brokerage_members_status_check;

alter table public.hof_brokerage_members
  add constraint hof_brokerage_members_status_check
  check (status in ('pending', 'active', 'suspended', 'removed'));

commit;

-- Verification
select
  b.id,
  b.name,
  b.slug,
  b.plan_name,
  b.user_cap,
  b.is_active
from public.hof_brokerages b
where b.slug = 'ondemand';
