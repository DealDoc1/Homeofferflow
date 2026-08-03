-- Replace per-row auth.uid() evaluation with a statement-stable initplan.
-- This is behavior-preserving and targets the policies flagged by the
-- Supabase performance advisor on 2026-08-03.

begin;

alter policy "hof_agent_profiles own insert"
  on public.hof_agent_profiles
  with check ((select auth.uid()) = user_id);
alter policy "hof_agent_profiles own read"
  on public.hof_agent_profiles
  using ((select auth.uid()) = user_id);
alter policy "hof_agent_profiles own update"
  on public.hof_agent_profiles
  using ((select auth.uid()) = user_id);

alter policy "hof_investor_profiles own insert"
  on public.hof_investor_profiles
  with check ((select auth.uid()) = user_id);
alter policy "hof_investor_profiles own read"
  on public.hof_investor_profiles
  using ((select auth.uid()) = user_id);
alter policy "hof_investor_profiles own update"
  on public.hof_investor_profiles
  using ((select auth.uid()) = user_id);

alter policy "Users can insert their own offer events"
  on public.hof_offer_events
  with check ((select auth.uid()) = user_id);
alter policy "Users can view their own offer events"
  on public.hof_offer_events
  using ((select auth.uid()) = user_id);

alter policy "Users can delete their own offers"
  on public.hof_offers
  using ((select auth.uid()) = user_id);
alter policy "Users can insert their own offers"
  on public.hof_offers
  with check ((select auth.uid()) = user_id);
alter policy "Users can update their own offers"
  on public.hof_offers
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
alter policy "Users can view their own offers"
  on public.hof_offers
  using ((select auth.uid()) = user_id);

alter policy "hof_seller_leads_insert_own"
  on public.hof_seller_leads
  with check ((select auth.uid()) = user_id);
alter policy "hof_seller_leads_select_own"
  on public.hof_seller_leads
  using ((select auth.uid()) = user_id);

alter policy "Users can insert their own usage"
  on public.hof_usage_events
  with check ((select auth.uid()) = user_id);
alter policy "Users can view their own usage"
  on public.hof_usage_events
  using ((select auth.uid()) = user_id);

commit;
