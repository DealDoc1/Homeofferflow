-- Brokerage logo storage. Logos are public-facing brand assets; brokerage
-- administrators can replace only their own brokerage's logo.

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'brokerage-branding',
  'brokerage-branding',
  true,
  2097152,
  array['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml']
)
on conflict (id) do update
set public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "brokerage_admins_manage_own_branding" on storage.objects;
create policy "brokerage_admins_manage_own_branding"
on storage.objects
for all
to authenticated
using (
  bucket_id = 'brokerage-branding'
  and exists (
    select 1
    from public.hof_profiles as profile
    where profile.id = (select auth.uid())
      and profile.brokerage_id::text = (storage.foldername(name))[1]
      and (
        coalesce(profile.is_brokerage_admin, false)
        or profile.role in ('broker', 'broker_admin', 'team_admin', 'team_lead')
      )
  )
)
with check (
  bucket_id = 'brokerage-branding'
  and exists (
    select 1
    from public.hof_profiles as profile
    where profile.id = (select auth.uid())
      and profile.brokerage_id::text = (storage.foldername(name))[1]
      and (
        coalesce(profile.is_brokerage_admin, false)
        or profile.role in ('broker', 'broker_admin', 'team_admin', 'team_lead')
      )
  )
);
