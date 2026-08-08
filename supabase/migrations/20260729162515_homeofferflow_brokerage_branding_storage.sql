-- Public brokerage logos with broker-admin-only upload and replacement rights.
-- The logo itself is intentionally public because it appears on public
-- brokerage launch pages. Browser writes remain confined to the active
-- broker administrator's own brokerage folder.

begin;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'brokerage-branding',
  'brokerage-branding',
  true,
  2097152,
  array['image/png', 'image/jpeg', 'image/webp']::text[]
)
on conflict (id) do update set
  public = true,
  file_size_limit = 2097152,
  allowed_mime_types = array['image/png', 'image/jpeg', 'image/webp']::text[];

drop policy if exists hof_brokerage_branding_storage_admin_manage on storage.objects;

create policy hof_brokerage_branding_storage_admin_manage
  on storage.objects for all to authenticated
  using (
    bucket_id = 'brokerage-branding'
    and storage.filename(name) in ('brand-logo.png', 'brand-logo.jpg', 'brand-logo.webp')
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
    bucket_id = 'brokerage-branding'
    and storage.filename(name) in ('brand-logo.png', 'brand-logo.jpg', 'brand-logo.webp')
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

