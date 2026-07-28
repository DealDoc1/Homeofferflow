-- HomeOfferFlow internal access seed
--
-- Platform administrators receive server-recorded free access. Brokerage
-- administrators remain limited to their own brokerage's reporting scope.

begin;

create schema if not exists private;

-- Give the three confirmed HomeOfferFlow platform admins their server-side
-- records now, without creating or changing any Stripe subscription.
insert into public.hof_platform_admins (user_id, label)
select u.id, lower(u.email)
from auth.users u
where lower(u.email) in (
  'andrew@ondemanddfw.com',
  'andrewchri@gmail.com',
  'support@homeofferflow.com'
)
on conflict (user_id) do update
set label = excluded.label;

insert into public.hof_subscriptions (
  user_id,
  role,
  plan,
  status,
  packet_limit,
  updated_at
)
select
  u.id,
  'agent',
  'platform_admin',
  'free_admin',
  1000,
  now()
from auth.users u
where lower(u.email) in (
  'andrew@ondemanddfw.com',
  'andrewchri@gmail.com',
  'support@homeofferflow.com'
)
on conflict (user_id) do update
set
  role = excluded.role,
  plan = excluded.plan,
  status = excluded.status,
  packet_limit = greatest(public.hof_subscriptions.packet_limit, excluded.packet_limit),
  updated_at = now();

-- If support@homeofferflow.com signs up later, seed that known internal
-- platform-admin account automatically. The trigger function is private and
-- is never callable from the browser.
create or replace function private.hof_seed_named_platform_admin()
returns trigger
language plpgsql
security definer
set search_path = public, pg_catalog
as $$
begin
  if lower(coalesce(new.email, '')) in (
    'andrew@ondemanddfw.com',
    'andrewchri@gmail.com',
    'support@homeofferflow.com'
  ) then
    insert into public.hof_platform_admins (user_id, label)
    values (new.id, lower(new.email))
    on conflict (user_id) do update
    set label = excluded.label;

    insert into public.hof_subscriptions (
      user_id,
      role,
      plan,
      status,
      packet_limit,
      updated_at
    )
    values (
      new.id,
      'agent',
      'platform_admin',
      'free_admin',
      1000,
      now()
    )
    on conflict (user_id) do update
    set
      role = excluded.role,
      plan = excluded.plan,
      status = excluded.status,
      packet_limit = greatest(public.hof_subscriptions.packet_limit, excluded.packet_limit),
      updated_at = now();
  end if;

  return new;
end;
$$;

revoke all on function private.hof_seed_named_platform_admin() from public, anon, authenticated;

drop trigger if exists hof_seed_named_platform_admin_after_signup on auth.users;
create trigger hof_seed_named_platform_admin_after_signup
  after insert on auth.users
  for each row
  execute function private.hof_seed_named_platform_admin();

-- Tyler is a free OnDemand brokerage administrator only. He is deliberately
-- not inserted into hof_platform_admins, so the global admin API remains
-- unavailable to him while brokerage-scoped reporting remains available.
insert into public.hof_subscriptions (
  user_id,
  role,
  plan,
  status,
  packet_limit,
  brokerage_id,
  launch_source,
  updated_at
)
select
  u.id,
  'agent',
  'brokerage_admin',
  'free_admin',
  1000,
  b.id,
  'ondemand_broker_admin',
  now()
from auth.users u
join public.hof_brokerages b on lower(b.slug) = 'ondemand'
where lower(u.email) = 'tyler@ondemanddfw.com'
on conflict (user_id) do update
set
  role = excluded.role,
  plan = excluded.plan,
  status = excluded.status,
  packet_limit = greatest(public.hof_subscriptions.packet_limit, excluded.packet_limit),
  brokerage_id = excluded.brokerage_id,
  launch_source = excluded.launch_source,
  updated_at = now();

commit;

-- Verification: platform admins are only the three named HomeOfferFlow
-- accounts; Tyler remains a brokerage-level administrator.
select
  u.email,
  case when pa.user_id is not null then 'platform_admin' else 'not_platform_admin' end as platform_scope,
  p.role as profile_role,
  m.role as membership_role,
  s.status as subscription_status,
  s.plan as subscription_plan,
  s.packet_limit
from auth.users u
left join public.hof_platform_admins pa on pa.user_id = u.id
left join public.hof_profiles p on p.id = u.id
left join public.hof_brokerage_members m on m.user_id = u.id
left join public.hof_subscriptions s on s.user_id = u.id
where lower(u.email) in (
  'andrew@ondemanddfw.com',
  'andrewchri@gmail.com',
  'support@homeofferflow.com',
  'tyler@ondemanddfw.com'
)
order by u.email;
