-- AI review snapshots are written through /api/save-ai-review, which verifies
-- the Supabase session and supplies the authoritative user_id server-side.
-- Remove direct authenticated Data API/GraphQL access while retaining the
-- service-role path used by the endpoint and platform admin feed.

begin;

revoke all on table public.hof_ai_offer_reviews from anon, authenticated;
grant all on table public.hof_ai_offer_reviews to service_role;

commit;
