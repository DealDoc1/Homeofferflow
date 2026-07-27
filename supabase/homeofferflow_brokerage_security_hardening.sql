-- HomeOfferFlow brokerage authorization hardening
-- Apply in the same coordinated production release as the updated index.html.
-- The application must stop writing role, brokerage_id, is_brokerage_admin,
-- and subscription state from the browser before this migration is applied.

begin;

-- Remove broad policies that exposed the brokerage directory and let browser
-- clients create authorization or billing state.
drop policy if exists hof_brokerages_select on public.hof_brokerages;
drop policy if exists hof_brokerages_insert on public.hof_brokerages;
drop policy if exists hof_brokerages_update on public.hof_brokerages;
drop policy if exists hof_brokerage_members_select on public.hof_brokerage_members;
drop policy if exists hof_brokerage_members_insert_own on public.hof_brokerage_members;
drop policy if exists hof_brokerage_invites_select on public.hof_brokerage_invites;
drop policy if exists hof_brokerage_invites_insert on public.hof_brokerage_invites;
drop policy if exists "hof_profiles own read" on public.hof_profiles;
drop policy if exists "hof_profiles own insert" on public.hof_profiles;
drop policy if exists "hof_profiles own update" on public.hof_profiles;
drop policy if exists "Users can insert their own subscription" on public.hof_subscriptions;
drop policy if exists "Users can update their own subscription" on public.hof_subscriptions;
drop policy if exists "Users can view their own subscription" on public.hof_subscriptions;
drop policy if exists hof_profiles_select_own on public.hof_profiles;
drop policy if exists hof_profiles_insert_own on public.hof_profiles;
drop policy if exists hof_profiles_update_own on public.hof_profiles;
drop policy if exists hof_brokerage_members_select_own on public.hof_brokerage_members;
drop policy if exists hof_brokerages_select_member on public.hof_brokerages;
drop policy if exists hof_subscriptions_select_own on public.hof_subscriptions;

alter table public.hof_brokerages enable row level security;
alter table public.hof_brokerage_members enable row level security;
alter table public.hof_brokerage_invites enable row level security;
alter table public.hof_profiles enable row level security;
alter table public.hof_subscriptions enable row level security;

create policy hof_profiles_select_own
  on public.hof_profiles for select to authenticated
  using ((select auth.uid()) = id);

create policy hof_profiles_insert_own
  on public.hof_profiles for insert to authenticated
  with check (
    (select auth.uid()) = id
    and role = 'agent'
    and brokerage_id is null
    and coalesce(is_brokerage_admin, false) = false
  );

create policy hof_profiles_update_own
  on public.hof_profiles for update to authenticated
  using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

create policy hof_brokerage_members_select_own
  on public.hof_brokerage_members for select to authenticated
  using ((select auth.uid()) = user_id);

create policy hof_brokerages_select_member
  on public.hof_brokerages for select to authenticated
  using (
    id = (
      select p.brokerage_id
      from public.hof_profiles p
      where p.id = (select auth.uid())
    )
  );

create policy hof_subscriptions_select_own
  on public.hof_subscriptions for select to authenticated
  using ((select auth.uid()) = user_id);

-- RLS chooses rows; column grants prevent browser-side role escalation and
-- fabricated payment/subscription state.
revoke all on table public.hof_profiles from anon, authenticated;
grant select on table public.hof_profiles to authenticated;
grant insert (id, email, team_name, created_at, updated_at)
  on table public.hof_profiles to authenticated;
grant update (email, team_name, updated_at)
  on table public.hof_profiles to authenticated;

revoke all on table public.hof_brokerages from anon, authenticated;
grant select on table public.hof_brokerages to authenticated;

revoke all on table public.hof_brokerage_members from anon, authenticated;
grant select on table public.hof_brokerage_members to authenticated;

revoke all on table public.hof_brokerage_invites from anon, authenticated;

revoke all on table public.hof_subscriptions from anon, authenticated;
grant select on table public.hof_subscriptions to authenticated;

grant all on table public.hof_profiles to service_role;
grant all on table public.hof_brokerages to service_role;
grant all on table public.hof_brokerage_members to service_role;
grant all on table public.hof_brokerage_invites to service_role;
grant all on table public.hof_subscriptions to service_role;

commit;
