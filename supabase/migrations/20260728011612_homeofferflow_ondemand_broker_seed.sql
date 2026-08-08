-- HomeOfferFlow OnDemand Realty broker seed
-- Tyler Demando and tyler@ondemanddfw.com were confirmed by the project owner.
-- This migration is idempotent and only applies when the matching Auth user exists.

begin;

insert into public.hof_profiles (
  id,
  email,
  role,
  brokerage_id,
  team_name,
  is_brokerage_admin,
  updated_at
)
select
  u.id,
  lower(u.email),
  'brokerage_admin',
  b.id,
  coalesce(b.dba_name, b.name, 'OnDemand Realty'),
  true,
  now()
from auth.users u
join public.hof_brokerages b
  on lower(b.slug) = 'ondemand'
where lower(u.email) = 'tyler@ondemanddfw.com'
on conflict (id) do update
set
  email = excluded.email,
  role = 'brokerage_admin',
  brokerage_id = excluded.brokerage_id,
  team_name = excluded.team_name,
  is_brokerage_admin = true,
  updated_at = now();

insert into public.hof_brokerage_members (
  brokerage_id,
  user_id,
  email,
  role,
  status,
  updated_at
)
select
  b.id,
  u.id,
  lower(u.email),
  'broker_admin',
  'active',
  now()
from auth.users u
join public.hof_brokerages b
  on lower(b.slug) = 'ondemand'
where lower(u.email) = 'tyler@ondemanddfw.com'
on conflict (brokerage_id, user_id) do update
set
  email = excluded.email,
  role = 'broker_admin',
  status = 'active',
  updated_at = now();

update public.hof_brokerages b
set
  created_by = u.id,
  contact_name = 'Tyler Demando',
  contact_email = 'tyler@ondemanddfw.com',
  updated_at = now()
from auth.users u
where lower(b.slug) = 'ondemand'
  and lower(u.email) = 'tyler@ondemanddfw.com';

commit;

