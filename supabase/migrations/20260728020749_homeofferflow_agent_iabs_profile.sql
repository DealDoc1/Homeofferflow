-- Agent-owned IABS profile document.
begin;

create table if not exists public.hof_agent_documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  document_type text not null check (document_type in ('iabs')),
  storage_bucket text not null default 'agent-documents'
    check (storage_bucket = 'agent-documents'),
  storage_path text not null,
  original_filename text not null,
  mime_type text not null default 'application/pdf'
    check (mime_type = 'application/pdf'),
  byte_size bigint not null check (byte_size > 0 and byte_size <= 10485760),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, document_type),
  check (storage_path = user_id::text || '/iabs.pdf')
);

create index if not exists hof_agent_documents_user_id_idx
  on public.hof_agent_documents (user_id);

alter table public.hof_agent_documents enable row level security;

drop policy if exists hof_agent_documents_select_own on public.hof_agent_documents;
drop policy if exists hof_agent_documents_insert_own on public.hof_agent_documents;
drop policy if exists hof_agent_documents_update_own on public.hof_agent_documents;
drop policy if exists hof_agent_documents_delete_own on public.hof_agent_documents;

create policy hof_agent_documents_select_own
  on public.hof_agent_documents for select to authenticated
  using ((select auth.uid()) = user_id);

create policy hof_agent_documents_insert_own
  on public.hof_agent_documents for insert to authenticated
  with check ((select auth.uid()) = user_id);

create policy hof_agent_documents_update_own
  on public.hof_agent_documents for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

create policy hof_agent_documents_delete_own
  on public.hof_agent_documents for delete to authenticated
  using ((select auth.uid()) = user_id);

revoke all on table public.hof_agent_documents from anon, authenticated;
grant select, insert, update, delete on table public.hof_agent_documents to authenticated;
grant all on table public.hof_agent_documents to service_role;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('agent-documents','agent-documents',false,10485760,array['application/pdf']::text[])
on conflict (id) do update set
  public = false,
  file_size_limit = 10485760,
  allowed_mime_types = array['application/pdf']::text[];

drop policy if exists hof_agent_documents_storage_select_own on storage.objects;
drop policy if exists hof_agent_documents_storage_insert_own on storage.objects;
drop policy if exists hof_agent_documents_storage_update_own on storage.objects;
drop policy if exists hof_agent_documents_storage_delete_own on storage.objects;

create policy hof_agent_documents_storage_select_own
  on storage.objects for select to authenticated
  using (bucket_id = 'agent-documents' and (storage.foldername(name))[1] = (select auth.uid()::text));

create policy hof_agent_documents_storage_insert_own
  on storage.objects for insert to authenticated
  with check (bucket_id = 'agent-documents' and (storage.foldername(name))[1] = (select auth.uid()::text));

create policy hof_agent_documents_storage_update_own
  on storage.objects for update to authenticated
  using (bucket_id = 'agent-documents' and (storage.foldername(name))[1] = (select auth.uid()::text))
  with check (bucket_id = 'agent-documents' and (storage.foldername(name))[1] = (select auth.uid()::text));

create policy hof_agent_documents_storage_delete_own
  on storage.objects for delete to authenticated
  using (bucket_id = 'agent-documents' and (storage.foldername(name))[1] = (select auth.uid()::text));

commit;

