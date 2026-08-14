-- Durable, versioned legal-policy acceptance records. These complement the
-- privacy-limited offer-event metric and are intentionally immutable from the
-- browser after creation.

begin;

create table if not exists public.hof_legal_acceptances (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  policy_version text not null check (char_length(trim(policy_version)) between 1 and 40),
  source text not null check (source in ('offer_wizard', 'ondemand_checkout')),
  accepted_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (user_id, policy_version)
);

create index if not exists hof_legal_acceptances_user_accepted_at_idx
  on public.hof_legal_acceptances (user_id, accepted_at desc);

alter table public.hof_legal_acceptances enable row level security;

revoke all on table public.hof_legal_acceptances from anon;
grant select, insert on table public.hof_legal_acceptances to authenticated;
grant all on table public.hof_legal_acceptances to service_role;

drop policy if exists hof_legal_acceptances_select_own on public.hof_legal_acceptances;
create policy hof_legal_acceptances_select_own
  on public.hof_legal_acceptances for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists hof_legal_acceptances_insert_own on public.hof_legal_acceptances;
create policy hof_legal_acceptances_insert_own
  on public.hof_legal_acceptances for insert to authenticated
  with check ((select auth.uid()) = user_id);

commit;
