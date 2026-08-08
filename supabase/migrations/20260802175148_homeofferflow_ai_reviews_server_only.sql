begin;
revoke all on table public.hof_ai_offer_reviews from anon, authenticated;
grant all on table public.hof_ai_offer_reviews to service_role;
commit;

