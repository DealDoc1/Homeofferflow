-- Standalone agreement records. These are intentionally separate from
-- hof_offers so buyer/tenant representation agreements cannot be mistaken for
-- purchase packets or exposed through brokerage aggregate reporting.

begin;

create table if not exists public.hof_standalone_agreements (
  id uuid primary key default gen_random_uuid(),
  brokerage_id uuid not null references public.hof_brokerages(id) on delete restrict,
  agent_user_id uuid not null references auth.users(id) on delete cascade,
  form_source_id uuid not null references public.hof_brokerage_form_sources(id) on delete restrict,
  form_code text not null check (form_code in ('TXR-1507')),
  source_revision text not null,
  status text not null default 'draft'
    check (status in ('draft', 'ready_for_review', 'sent', 'signed', 'void', 'failed')),
  client_names jsonb not null check (jsonb_typeof(client_names) = 'array' and jsonb_array_length(client_names) between 1 and 2),
  agreement_data jsonb not null default '{}'::jsonb check (jsonb_typeof(agreement_data) = 'object'),
  signwell_document_id text,
  signwell_status text,
  generated_storage_bucket text,
  generated_storage_path text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  sent_at timestamptz,
  signed_at timestamptz,
  unique (signwell_document_id)
);

create index if not exists hof_standalone_agreements_agent_idx
  on public.hof_standalone_agreements (agent_user_id, created_at desc);
create index if not exists hof_standalone_agreements_brokerage_status_idx
  on public.hof_standalone_agreements (brokerage_id, status, created_at desc);

alter table public.hof_standalone_agreements enable row level security;

-- The assigned agent can read their own agreement records. Broker dashboards
-- remain aggregate-only unless a later, explicitly approved record-access
-- design is implemented.
drop policy if exists hof_standalone_agreements_select_own on public.hof_standalone_agreements;
create policy hof_standalone_agreements_select_own
  on public.hof_standalone_agreements for select to authenticated
  using ((select auth.uid()) = agent_user_id);

-- Browser-side edits are limited to the agent's own drafts. The server moves
-- an agreement into review/sent/signed states after source validation and the
-- SignWell flow are implemented.
drop policy if exists hof_standalone_agreements_insert_own_draft on public.hof_standalone_agreements;
create policy hof_standalone_agreements_insert_own_draft
  on public.hof_standalone_agreements for insert to authenticated
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
        and p.brokerage_id = hof_standalone_agreements.brokerage_id
    )
  );

drop policy if exists hof_standalone_agreements_update_own_draft on public.hof_standalone_agreements;
create policy hof_standalone_agreements_update_own_draft
  on public.hof_standalone_agreements for update to authenticated
  using ((select auth.uid()) = agent_user_id and status = 'draft')
  with check ((select auth.uid()) = agent_user_id and status = 'draft');

drop policy if exists hof_standalone_agreements_delete_own_draft on public.hof_standalone_agreements;
create policy hof_standalone_agreements_delete_own_draft
  on public.hof_standalone_agreements for delete to authenticated
  using ((select auth.uid()) = agent_user_id and status = 'draft');

revoke all on table public.hof_standalone_agreements from anon;
grant select, insert, update, delete on table public.hof_standalone_agreements to authenticated;
grant all on table public.hof_standalone_agreements to service_role;

commit;

-- Verification after applying:
-- select status, count(*) from public.hof_standalone_agreements group by status;


