-- Seller/listing workspace foundation. This is deliberately separate from
-- buyer offers and standalone agreement drafts. It stores agent-owned listing
-- intake only; it does not create, send, or sign a listing/disclosure form.

begin;

create table if not exists public.hof_listing_workspaces (
  id uuid primary key default gen_random_uuid(),
  brokerage_id uuid not null references public.hof_brokerages(id) on delete cascade,
  agent_user_id uuid not null references auth.users(id) on delete cascade,
  seller_lead_id uuid references public.hof_seller_leads(id) on delete set null,
  listing_kind text not null check (listing_kind in ('sale', 'lease')),
  property_address text not null check (length(trim(property_address)) between 3 and 400),
  seller_names text[] not null check (cardinality(seller_names) between 1 and 4),
  status text not null default 'intake'
    check (status in ('intake', 'source_pending', 'draft', 'ready_for_review', 'archived')),
  requested_workflows jsonb not null default '[]'::jsonb
    check (jsonb_typeof(requested_workflows) = 'array'),
  confidential_notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists hof_listing_workspaces_agent_idx
  on public.hof_listing_workspaces (agent_user_id, updated_at desc);
create index if not exists hof_listing_workspaces_brokerage_status_idx
  on public.hof_listing_workspaces (brokerage_id, status, updated_at desc);

alter table public.hof_listing_workspaces enable row level security;

drop policy if exists hof_listing_workspaces_agent_select_own on public.hof_listing_workspaces;
create policy hof_listing_workspaces_agent_select_own
  on public.hof_listing_workspaces for select to authenticated
  using (agent_user_id = (select auth.uid()));

drop policy if exists hof_listing_workspaces_agent_insert_own on public.hof_listing_workspaces;
create policy hof_listing_workspaces_agent_insert_own
  on public.hof_listing_workspaces for insert to authenticated
  with check (
    agent_user_id = (select auth.uid())
    and exists (
      select 1 from public.hof_profiles p
      join public.hof_brokerage_members m
        on m.user_id = p.id and m.brokerage_id = p.brokerage_id
       and m.status = 'active'
      where p.id = (select auth.uid()) and p.brokerage_id = hof_listing_workspaces.brokerage_id
    )
  );

drop policy if exists hof_listing_workspaces_agent_update_own on public.hof_listing_workspaces;
create policy hof_listing_workspaces_agent_update_own
  on public.hof_listing_workspaces for update to authenticated
  using (agent_user_id = (select auth.uid()))
  with check (agent_user_id = (select auth.uid()));

-- A brokerage administrator receives only operational totals through this
-- function, never seller names, addresses, notes, or financial details.
create or replace function public.hof_brokerage_listing_workspace_summary()
returns table (listing_kind text, status text, workspace_count bigint)
language sql security definer set search_path = public
as $$
  select w.listing_kind, w.status, count(*)::bigint
  from public.hof_listing_workspaces w
  where exists (
    select 1 from public.hof_profiles p
    join public.hof_brokerage_members m
      on m.user_id = p.id and m.brokerage_id = p.brokerage_id
     and m.status = 'active' and m.role in ('broker_admin', 'owner')
    where p.id = (select auth.uid())
      and p.brokerage_id = w.brokerage_id
      and (p.is_brokerage_admin = true or p.role = 'brokerage_admin')
  )
  group by w.listing_kind, w.status
  order by w.listing_kind, w.status;
$$;

revoke all on public.hof_listing_workspaces from anon;
grant select, insert, update on public.hof_listing_workspaces to authenticated;
revoke all on function public.hof_brokerage_listing_workspace_summary() from public;
grant execute on function public.hof_brokerage_listing_workspace_summary() to authenticated;

commit;
