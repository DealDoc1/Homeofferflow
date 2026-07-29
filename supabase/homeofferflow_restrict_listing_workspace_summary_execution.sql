-- Security repair: the broker listing summary is intentionally callable only
-- by signed-in users. The function itself applies the brokerage-admin check.
-- Explicitly revoking PUBLIC prevents anonymous REST/RPC execution.

begin;

revoke all on function public.hof_brokerage_listing_workspace_summary() from public;
revoke all on function public.hof_brokerage_listing_workspace_summary() from anon;
grant execute on function public.hof_brokerage_listing_workspace_summary() to authenticated;

commit;

-- Verification:
-- select
--   has_function_privilege('anon', 'public.hof_brokerage_listing_workspace_summary()', 'execute') as anon_can_execute,
--   has_function_privilege('authenticated', 'public.hof_brokerage_listing_workspace_summary()', 'execute') as authenticated_can_execute;
