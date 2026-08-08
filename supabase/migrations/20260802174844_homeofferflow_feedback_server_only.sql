begin;
revoke all on table public.hof_feedback from anon, authenticated;
grant all on table public.hof_feedback to service_role;
commit;

