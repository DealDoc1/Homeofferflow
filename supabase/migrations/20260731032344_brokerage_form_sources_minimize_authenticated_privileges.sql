-- Follow-up hardening for the private brokerage source registry. The browser
-- upload flow needs writes only; it must not retain table-level metadata or
-- schema-management privileges inherited from the original broad grant.

begin;

revoke all on table public.hof_brokerage_form_sources from authenticated;
grant insert, update, delete on table public.hof_brokerage_form_sources to authenticated;
grant all on table public.hof_brokerage_form_sources to service_role;

commit;

