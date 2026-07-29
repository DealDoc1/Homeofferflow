-- HomeOfferFlow private browser tables: remove anonymous Data API access
--
-- Each table below already uses owner-scoped RLS policies that require
-- auth.uid(). The live application only calls them after sign-in. Revoking
-- anon privileges therefore removes public schema discovery without changing
-- authenticated, owner-scoped workflows or service-role operations.

begin;

revoke all on table
  public.hof_agent_profiles,
  public.hof_ai_offer_reviews,
  public.hof_feedback,
  public.hof_investor_profiles,
  public.hof_offer_events,
  public.hof_offers,
  public.hof_seller_leads,
  public.hof_usage_events
from anon;

commit;
