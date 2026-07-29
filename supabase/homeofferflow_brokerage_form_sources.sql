-- Private brokerage-owned source forms for future non-TREC workflows.
--
-- This does NOT distribute or activate a Texas REALTORS form. A brokerage
-- administrator must upload its own authorized source and attest to authority
-- before a separate workflow can use it. Source PDFs stay in private Storage.

begin;

create table if not exists public.hof_brokerage_form_sources (
  id uuid primary key default gen_random_uuid(),
  brokerage_id uuid not null references public.hof_brokerages(id) on delete cascade,
  form_code text not null check (form_code in ('TXR-1501', 'TXR-1506', 'TXR-1507', 'TXR-1508')),
  source_revision text not null,
  status text not null default 'draft'
    check (status in ('draft', 'approved', 'retired')),
  storage_bucket text not null default 'brokerage-form-sources'
    check (storage_bucket = 'brokerage-form-sources'),
  storage_path text not null,
  original_filename text not null,
  mime_type text not null default 'application/pdf'
    check (mime_type = 'application/pdf'),
  byte_size bigint not null check (byte_size > 0 and byte_size <= 10485760),
  authorization_attested boolean not null default false,
  authorized_by_user_id uuid references auth.users(id) on delete set null,
  authorized_at timestamptz,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (
    storage_path like brokerage_id::text || '/%' || '.pdf'
  ),
  check (
    (authorization_attested = false and authorized_at is null)
    or (authorization_attested = true and authorized_by_user_id is not null and authorized_at is not null)
  )
);

create unique index if not exists hof_brokerage_form_sources_active_revision_idx
  on public.hof_brokerage_form_sources (brokerage_id, form_code, source_revision)
  where status <> 'retired';

create index if not exists hof_brokerage_form_sources_brokerage_idx
  on public.hof_brokerage_form_sources (brokerage_id, form_code, status);

alter table public.hof_brokerage_form_sources enable row level security;

-- Only the brokerage's active broker administrators can manage source files.
drop policy if exists hof_brokerage_form_sources_admin_manage on public.hof_brokerage_form_sources;
create policy hof_brokerage_form_sources_admin_manage
  on public.hof_brokerage_form_sources for all to authenticated
  using (
    exists (
      select 1
      from public.hof_profiles p
      join public.hof_brokerage_members m
        on m.user_id = p.id
       and m.brokerage_id = p.brokerage_id
       and m.status = 'active'
       and m.role in ('broker_admin', 'owner')
      where p.id = (select auth.uid())
        and p.brokerage_id = hof_brokerage_form_sources.brokerage_id
        and (p.is_brokerage_admin = true or p.role = 'brokerage_admin')
    )
  )
  with check (
    authorization_attested = true
    and authorized_by_user_id = (select auth.uid())
    and exists (
      select 1
      from public.hof_profiles p
      join public.hof_brokerage_members m
        on m.user_id = p.id
       and m.brokerage_id = p.brokerage_id
       and m.status = 'active'
       and m.role in ('broker_admin', 'owner')
      where p.id = (select auth.uid())
        and p.brokerage_id = hof_brokerage_form_sources.brokerage_id
        and (p.is_brokerage_admin = true or p.role = 'brokerage_admin')
    )
  );

-- Agents can see that their brokerage has an approved source for a workflow,
-- but cannot download or read a restricted source PDF from the browser.
drop policy if exists hof_brokerage_form_sources_agent_select_approved on public.hof_brokerage_form_sources;
create policy hof_brokerage_form_sources_agent_select_approved
  on public.hof_brokerage_form_sources for select to authenticated
  using (
    status = 'approved'
    and authorization_attested = true
    and exists (
      select 1
      from public.hof_profiles p
      join public.hof_brokerage_members m
        on m.user_id = p.id
       and m.brokerage_id = p.brokerage_id
       and m.status = 'active'
      where p.id = (select auth.uid())
        and p.brokerage_id = hof_brokerage_form_sources.brokerage_id
    )
  );

revoke all on table public.hof_brokerage_form_sources from anon;
grant select, insert, update, delete on table public.hof_brokerage_form_sources to authenticated;
grant all on table public.hof_brokerage_form_sources to service_role;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'brokerage-form-sources',
  'brokerage-form-sources',
  false,
  10485760,
  array['application/pdf']::text[]
)
on conflict (id) do update set
  public = false,
  file_size_limit = 10485760,
  allowed_mime_types = array['application/pdf']::text[];

-- The browser can only manage PDFs inside its own brokerage folder when the
-- user is an active broker administrator. Agents never get Storage access to
-- source forms; form-generation APIs use the server service role later.
drop policy if exists hof_brokerage_form_sources_storage_admin_manage on storage.objects;
create policy hof_brokerage_form_sources_storage_admin_manage
  on storage.objects for all to authenticated
  using (
    bucket_id = 'brokerage-form-sources'
    and exists (
      select 1
      from public.hof_profiles p
      join public.hof_brokerage_members m
        on m.user_id = p.id
       and m.brokerage_id = p.brokerage_id
       and m.status = 'active'
       and m.role in ('broker_admin', 'owner')
      where p.id = (select auth.uid())
        and p.brokerage_id::text = (storage.foldername(name))[1]
        and (p.is_brokerage_admin = true or p.role = 'brokerage_admin')
    )
  )
  with check (
    bucket_id = 'brokerage-form-sources'
    and exists (
      select 1
      from public.hof_profiles p
      join public.hof_brokerage_members m
        on m.user_id = p.id
       and m.brokerage_id = p.brokerage_id
       and m.status = 'active'
       and m.role in ('broker_admin', 'owner')
      where p.id = (select auth.uid())
        and p.brokerage_id::text = (storage.foldername(name))[1]
        and (p.is_brokerage_admin = true or p.role = 'brokerage_admin')
    )
  );

commit;

-- Verification after applying:
-- select form_code, source_revision, status, authorization_attested
-- from public.hof_brokerage_form_sources
-- where brokerage_id = (select id from public.hof_brokerages where slug = 'ondemand');
