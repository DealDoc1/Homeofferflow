-- AI review snapshots are written through the existing
-- /api/ai-offer-review save_snapshot action, which verifies the Supabase
-- session and supplies the authoritative user_id server-side.

begin;

revoke all on table public.hof_ai_offer_reviews from anon, authenticated;
grant all on table public.hof_ai_offer_reviews to service_role;

commit;
