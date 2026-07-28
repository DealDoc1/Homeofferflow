-- Tyler Demando is the OnDemand brokerage administrator, not a HomeOfferFlow
-- platform administrator.  He must start the same card-required 60-day
-- OnDemand Stripe trial as every other participating agent.
--
-- This intentionally preserves his brokerage_admin profile and active
-- broker_admin membership.  It only removes the server-side free-access
-- subscription override that would otherwise bypass Stripe billing.

begin;

update public.hof_subscriptions as s
set
  role = 'agent',
  plan = 'agent_starter_monthly',
  status = 'canceled',
  packet_limit = 10,
  trial_started_at = null,
  trial_ends_at = null,
  launch_source = 'ondemand_checkout_required',
  updated_at = now()
from auth.users as u
join public.hof_brokerages as b
  on lower(b.slug) = 'ondemand'
where s.user_id = u.id
  and lower(u.email) = 'tyler@ondemanddfw.com'
  and s.brokerage_id = b.id;

commit;

-- Verification: Tyler is brokerage-scoped, has no free-access subscription,
-- and can begin the normal OnDemand Stripe trial through /ondemand.
select
  lower(u.email) as email,
  p.role as profile_role,
  m.role as membership_role,
  m.status as membership_status,
  s.plan as subscription_plan,
  s.status as subscription_status,
  s.launch_source,
  s.stripe_customer_id,
  s.stripe_subscription_id,
  b.slug as brokerage_slug
from auth.users as u
join public.hof_profiles as p on p.id = u.id
join public.hof_brokerage_members as m on m.user_id = u.id
join public.hof_subscriptions as s on s.user_id = u.id
join public.hof_brokerages as b on b.id = s.brokerage_id
where lower(u.email) = 'tyler@ondemanddfw.com';
