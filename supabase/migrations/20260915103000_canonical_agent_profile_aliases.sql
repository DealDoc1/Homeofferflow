-- Approved alternate sign-ins read and update one canonical agent profile.
-- Client roles can only read their own alias row; alias assignment remains an
-- administrative operation, avoiding arbitrary cross-account profile access.

create table if not exists public.hof_agent_profile_aliases (
  login_user_id uuid primary key references public.hof_profiles(id) on delete cascade,
  canonical_user_id uuid not null references public.hof_agent_profiles(user_id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint hof_agent_profile_aliases_not_self check (login_user_id <> canonical_user_id)
);

alter table public.hof_agent_profile_aliases enable row level security;
revoke all on table public.hof_agent_profile_aliases from anon, authenticated;
grant select on table public.hof_agent_profile_aliases to authenticated;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'hof_agent_profile_aliases'
      and policyname = 'hof_agent_profile_aliases own read'
  ) then
    create policy "hof_agent_profile_aliases own read"
      on public.hof_agent_profile_aliases
      for select to authenticated
      using ((select auth.uid()) = login_user_id);
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'hof_agent_profiles'
      and policyname = 'hof_agent_profiles linked profile read'
  ) then
    create policy "hof_agent_profiles linked profile read"
      on public.hof_agent_profiles
      for select to authenticated
      using (exists (
        select 1 from public.hof_agent_profile_aliases alias
        where alias.login_user_id = (select auth.uid())
          and alias.canonical_user_id = hof_agent_profiles.user_id
      ));
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'hof_agent_profiles'
      and policyname = 'hof_agent_profiles linked profile update'
  ) then
    create policy "hof_agent_profiles linked profile update"
      on public.hof_agent_profiles
      for update to authenticated
      using (exists (
        select 1 from public.hof_agent_profile_aliases alias
        where alias.login_user_id = (select auth.uid())
          and alias.canonical_user_id = hof_agent_profiles.user_id
      ))
      with check (exists (
        select 1 from public.hof_agent_profile_aliases alias
        where alias.login_user_id = (select auth.uid())
          and alias.canonical_user_id = hof_agent_profiles.user_id
      ));
  end if;
end
$$;

insert into public.hof_agent_profile_aliases (login_user_id, canonical_user_id)
values ('3e8c1d3c-c085-477a-92be-a8c482b09c5b', 'b5700a9d-a78c-497b-aef9-c3e4f6872dc2')
on conflict (login_user_id) do update
set canonical_user_id = excluded.canonical_user_id,
    updated_at = now();
