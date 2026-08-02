-- HomeOfferFlow feedback is now written and read through server-side routes.
-- Keep customer feedback out of the authenticated GraphQL/Data API surface.

begin;

revoke all on table public.hof_feedback from anon, authenticated;
grant all on table public.hof_feedback to service_role;

commit;
