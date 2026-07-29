-- Security hardening for the brokerage listing-workspace summary.
--
-- The browser now receives aggregate counts through /api/admin-dashboard after
-- server-side brokerage-admin authorization. Apply this only in the same
-- intentional release as that browser/API code; applying it earlier would
-- break the older browser RPC call.

begin;

revoke all on function public.hof_brokerage_listing_workspace_summary() from public;
revoke all on function public.hof_brokerage_listing_workspace_summary() from anon;
revoke all on function public.hof_brokerage_listing_workspace_summary() from authenticated;
grant execute on function public.hof_brokerage_listing_workspace_summary() to service_role;

commit;

-- Post-release verification:
-- select
--   has_function_privilege('anon', 'public.hof_brokerage_listing_workspace_summary()', 'execute') as anon_can_execute,
--   has_function_privilege('authenticated', 'public.hof_brokerage_listing_workspace_summary()', 'execute') as authenticated_can_execute,
--   has_function_privilege('service_role', 'public.hof_brokerage_listing_workspace_summary()', 'execute') as service_role_can_execute;
