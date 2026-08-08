begin;

revoke all on function public.hof_brokerage_listing_workspace_summary() from public;
revoke all on function public.hof_brokerage_listing_workspace_summary() from anon;
revoke all on function public.hof_brokerage_listing_workspace_summary() from authenticated;
grant execute on function public.hof_brokerage_listing_workspace_summary() to service_role;

commit;

