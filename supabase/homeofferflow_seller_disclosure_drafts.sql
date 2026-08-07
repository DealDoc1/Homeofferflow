-- Seller disclosure draft foundation for the supplied TREC-55-1 and TREC-61-0
-- sources. This stores structured seller responses and source references only.
-- It does not render, send, or sign a seller disclosure.

begin;

create table if not exists public.hof_seller_disclosure_drafts (
  id uuid primary key default gen_random_uuid(),
  brokerage_id uuid not null references public.hof_brokerages(id) on delete restrict,
  agent_user_id uuid not null references auth.users(id) on delete cascade,
  listing_workspace_id uuid references public.hof_listing_workspaces(id) on delete set null,
  disclosure_source_id uuid not null references public.hof_brokerage_form_sources(id) on delete restrict,
  water_source_id uuid references public.hof_brokerage_form_sources(id) on delete restrict,
  disclosure_source_revision text not null,
  water_source_revision text,
  status text not null default 'draft'
    check (status in ('draft', 'ready_for_review', 'void')),
  property_address text not null
    check (length(btrim(property_address)) between 3 and 400),
  seller_names jsonb not null
    check (jsonb_typeof(seller_names) = 'array' and jsonb_array_length(seller_names) between 1 and 2),
  buyer_names jsonb not null default '[]'::jsonb
    check (jsonb_typeof(buyer_names) = 'array' and jsonb_array_length(buyer_names) between 0 and 2),
  response_data jsonb not null default '{}'::jsonb
    check (jsonb_typeof(response_data) = 'object'),
  water_rights_data jsonb not null default '{}'::jsonb
    check (jsonb_typeof(water_rights_data) = 'object'),
  seller_review_attested boolean not null default false,
  seller_review_attested_at timestamptz,
  seller_review_attested_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (
    (seller_review_attested = false and seller_review_attested_at is null and seller_review_attested_by is null)
    or
    (seller_review_attested = true and seller_review_attested_at is not null and seller_review_attested_by is not null)
  )
);

create index if not exists hof_seller_disclosure_drafts_agent_idx
  on public.hof_seller_disclosure_drafts (agent_user_id, updated_at desc);

create index if not exists hof_seller_disclosure_drafts_brokerage_idx
  on public.hof_seller_disclosure_drafts (brokerage_id, status, updated_at desc);

alter table public.hof_seller_disclosure_drafts enable row level security;

drop policy if exists hof_seller_disclosure_drafts_select_own
  on public.hof_seller_disclosure_drafts;
create policy hof_seller_disclosure_drafts_select_own
  on public.hof_seller_disclosure_drafts for select to authenticated
  using ((select auth.uid()) = agent_user_id);

drop policy if exists hof_seller_disclosure_drafts_insert_own
  on public.hof_seller_disclosure_drafts;
create policy hof_seller_disclosure_drafts_insert_own
  on public.hof_seller_disclosure_drafts for insert to authenticated
  with check (
    (select auth.uid()) = agent_user_id
    and status = 'draft'
    and exists (
      select 1
      from public.hof_profiles p
      join public.hof_brokerage_members m
        on m.user_id = p.id
       and m.brokerage_id = p.brokerage_id
       and m.status = 'active'
      where p.id = (select auth.uid())
        and p.brokerage_id = hof_seller_disclosure_drafts.brokerage_id
    )
  );

drop policy if exists hof_seller_disclosure_drafts_update_own
  on public.hof_seller_disclosure_drafts;
create policy hof_seller_disclosure_drafts_update_own
  on public.hof_seller_disclosure_drafts for update to authenticated
  using ((select auth.uid()) = agent_user_id and status in ('draft', 'ready_for_review'))
  with check (
    (select auth.uid()) = agent_user_id
    and status in ('draft', 'ready_for_review')
  );

drop policy if exists hof_seller_disclosure_drafts_delete_own
  on public.hof_seller_disclosure_drafts;
create policy hof_seller_disclosure_drafts_delete_own
  on public.hof_seller_disclosure_drafts for delete to authenticated
  using ((select auth.uid()) = agent_user_id and status = 'draft');

revoke all on public.hof_seller_disclosure_drafts from anon;
grant select, insert, update, delete on public.hof_seller_disclosure_drafts to authenticated;
grant all on public.hof_seller_disclosure_drafts to service_role;

commit;
