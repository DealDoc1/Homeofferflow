-- Restrict agent IABS storage to the one profile object represented by the database check constraint.
begin;
drop policy if exists hof_agent_documents_storage_select_own on storage.objects;
drop policy if exists hof_agent_documents_storage_insert_own on storage.objects;
drop policy if exists hof_agent_documents_storage_update_own on storage.objects;
drop policy if exists hof_agent_documents_storage_delete_own on storage.objects;
create policy hof_agent_documents_storage_select_own
  on storage.objects for select to authenticated
  using (bucket_id = 'agent-documents' and name = (select auth.uid()::text || '/iabs.pdf'));
create policy hof_agent_documents_storage_insert_own
  on storage.objects for insert to authenticated
  with check (bucket_id = 'agent-documents' and name = (select auth.uid()::text || '/iabs.pdf'));
create policy hof_agent_documents_storage_update_own
  on storage.objects for update to authenticated
  using (bucket_id = 'agent-documents' and name = (select auth.uid()::text || '/iabs.pdf'))
  with check (bucket_id = 'agent-documents' and name = (select auth.uid()::text || '/iabs.pdf'));
create policy hof_agent_documents_storage_delete_own
  on storage.objects for delete to authenticated
  using (bucket_id = 'agent-documents' and name = (select auth.uid()::text || '/iabs.pdf'));
commit;

