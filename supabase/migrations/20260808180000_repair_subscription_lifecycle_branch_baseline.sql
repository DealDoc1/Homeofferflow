-- Keep subscription lifecycle replay safe on schema-only Supabase branch
-- baselines. Production already relies on these invariants; IF NOT EXISTS and
-- idempotent policy replacement make this safe to apply to both environments.

create unique index if not exists hof_subscriptions_user_id_key
  on public.hof_subscriptions(user_id);

create index if not exists hof_stripe_webhook_events_received_at_idx
  on public.hof_stripe_webhook_events(received_at desc);
create index if not exists hof_stripe_webhook_events_state_received_idx
  on public.hof_stripe_webhook_events(processing_state, received_at desc);
create index if not exists hof_stripe_webhook_events_subscription_idx
  on public.hof_stripe_webhook_events(stripe_subscription_id);

alter table public.hof_stripe_webhook_events enable row level security;
revoke all on table public.hof_stripe_webhook_events from anon, authenticated;
grant all on table public.hof_stripe_webhook_events to service_role;
drop policy if exists stripe_webhook_events_server_only on public.hof_stripe_webhook_events;
create policy stripe_webhook_events_server_only
  on public.hof_stripe_webhook_events for all to authenticated
  using (false) with check (false);

alter table public.hof_subscriptions enable row level security;
revoke all on table public.hof_subscriptions from anon, authenticated;
grant select on public.hof_subscriptions to authenticated;
grant all on public.hof_subscriptions to service_role;
drop policy if exists hof_subscriptions_select_own on public.hof_subscriptions;
create policy hof_subscriptions_select_own
  on public.hof_subscriptions for select to authenticated
  using ((select auth.uid()) = user_id);

alter table public.hof_brokerage_members enable row level security;
revoke all on table public.hof_brokerage_members from anon, authenticated;
grant select on public.hof_brokerage_members to authenticated;
grant all on table public.hof_brokerage_members to service_role;
drop policy if exists hof_brokerage_members_select_own on public.hof_brokerage_members;
create policy hof_brokerage_members_select_own
  on public.hof_brokerage_members for select to authenticated
  using ((select auth.uid()) = user_id);
