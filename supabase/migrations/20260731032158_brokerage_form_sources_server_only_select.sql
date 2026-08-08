-- Keep private brokerage form-source metadata behind the authenticated server
-- endpoint. Agents and broker admins still use the existing browser insert /
-- storage policies, but the raw table is no longer directly selectable by
-- authenticated clients or exposed through the GraphQL table surface.

begin;

drop policy if exists hof_brokerage_form_sources_agent_select_approved
  on public.hof_brokerage_form_sources;

revoke select on table public.hof_brokerage_form_sources from authenticated;
grant insert, update, delete on table public.hof_brokerage_form_sources to authenticated;
grant all on table public.hof_brokerage_form_sources to service_role;

comment on table public.hof_brokerage_form_sources is
  'Private brokerage source registry. Read access is server-only; browser clients receive sanitized readiness metadata from /api/admin-dashboard.';

commit;

