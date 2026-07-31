-- Private generated PDFs for standalone brokerage agreements.
-- Source forms and generated drafts are separate objects. The server uses the
-- service role to fetch the approved source and write a generated draft; the
-- browser receives only a short-lived signed URL for the agent's own draft.

begin;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'brokerage-generated-agreements',
  'brokerage-generated-agreements',
  false,
  10485760,
  array['application/pdf']::text[]
)
on conflict (id) do update set
  public = false,
  file_size_limit = 10485760,
  allowed_mime_types = array['application/pdf']::text[];

drop policy if exists hof_generated_agreements_agent_select_own on storage.objects;
create policy hof_generated_agreements_agent_select_own
  on storage.objects for select to authenticated
  using (
    bucket_id = 'brokerage-generated-agreements'
    and (storage.foldername(name))[2] = (select auth.uid())::text
    and exists (
      select 1
      from public.hof_profiles p
      join public.hof_brokerage_members m
        on m.user_id = p.id
       and m.brokerage_id = p.brokerage_id
       and m.status = 'active'
      where p.id = (select auth.uid())
        and p.brokerage_id::text = (storage.foldername(name))[1]
    )
  );

-- Generated objects are written only by the server service role.
drop policy if exists hof_generated_agreements_agent_insert on storage.objects;
drop policy if exists hof_generated_agreements_agent_update on storage.objects;
drop policy if exists hof_generated_agreements_agent_delete on storage.objects;

commit;

-- Verification:
-- select id, public, file_size_limit from storage.buckets
-- where id = 'brokerage-generated-agreements';
