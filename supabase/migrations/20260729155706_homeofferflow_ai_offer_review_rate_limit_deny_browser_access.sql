begin; drop policy if exists hof_ai_offer_review_rate_limits_deny_browser on public.hof_ai_offer_review_rate_limits; create policy hof_ai_offer_review_rate_limits_deny_browser on public.hof_ai_offer_review_rate_limits for all to anon, authenticated using (false) with check (false); commit;

