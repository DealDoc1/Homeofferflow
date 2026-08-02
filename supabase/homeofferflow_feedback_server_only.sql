-- HomeOfferFlow feedback is now written and read through server-side routes.
-- Keep customer feedback out of the authenticated GraphQL/Data API surface.
-- service_role remains available to /api/submit-feedback and the platform
-- admin feed; the browser must use those routes instead of the table.

begin;

revoke all on table public.hof_feedback from anon, authenticated;
grant all on table public.hof_feedback to service_role;

commit;
