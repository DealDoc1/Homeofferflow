-- Explicit deny policy for the private brokerage-invites table.
-- Privileges are already revoked from browser roles; this policy supplies
-- defense in depth and documents that all browser access is intentionally off.

begin;

drop policy if exists hof_brokerage_invites_deny_browser on public.hof_brokerage_invites;

create policy hof_brokerage_invites_deny_browser
  on public.hof_brokerage_invites
  as restrictive
  for all
  to anon, authenticated
  using (false)
  with check (false);

commit;


