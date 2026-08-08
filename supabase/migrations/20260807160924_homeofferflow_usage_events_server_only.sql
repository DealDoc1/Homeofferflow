begin;
alter table public.hof_usage_events enable row level security;
drop policy if exists "Users can insert their own usage" on public.hof_usage_events;
drop policy if exists "Users can view their own usage" on public.hof_usage_events;
revoke all on table public.hof_usage_events from anon, authenticated;
grant all on table public.hof_usage_events to service_role;
commit;

