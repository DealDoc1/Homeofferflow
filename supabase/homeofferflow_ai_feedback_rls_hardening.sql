-- Restrict private AI-review and feedback tables to the authenticated
-- workflows that actually use them. The application writes feedback through
-- a service-role API route and writes AI review snapshots directly as the
-- signed-in owner; anonymous access is never required.

begin;

alter table public.hof_ai_offer_reviews enable row level security;
drop policy if exists hof_ai_offer_reviews_insert_own on public.hof_ai_offer_reviews;
drop policy if exists hof_ai_offer_reviews_select_own on public.hof_ai_offer_reviews;
create policy hof_ai_offer_reviews_insert_own
  on public.hof_ai_offer_reviews for insert to authenticated
  with check ((select auth.uid()) = user_id);
create policy hof_ai_offer_reviews_select_own
  on public.hof_ai_offer_reviews for select to authenticated
  using ((select auth.uid()) = user_id);
revoke all on table public.hof_ai_offer_reviews from anon, authenticated;
grant select, insert on table public.hof_ai_offer_reviews to authenticated;
grant all on table public.hof_ai_offer_reviews to service_role;

alter table public.hof_feedback enable row level security;
drop policy if exists hof_feedback_insert_authenticated on public.hof_feedback;
drop policy if exists hof_feedback_select_own on public.hof_feedback;
create policy hof_feedback_insert_authenticated
  on public.hof_feedback for insert to authenticated
  with check ((select auth.uid()) = user_id);
create policy hof_feedback_select_own
  on public.hof_feedback for select to authenticated
  using ((select auth.uid()) = user_id);
revoke all on table public.hof_feedback from anon, authenticated;
grant select, insert on table public.hof_feedback to authenticated;
grant all on table public.hof_feedback to service_role;

commit;
