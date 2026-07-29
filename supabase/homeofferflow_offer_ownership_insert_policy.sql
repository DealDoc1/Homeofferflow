-- HomeOfferFlow offer ownership hardening
--
-- A duplicate legacy insert policy allowed a browser caller to create an offer
-- with user_id = null. Normal offer saving always has an authenticated owner;
-- server-side generation uses service_role and is unaffected by this removal.

begin;

drop policy if exists "hof_offers own insert" on public.hof_offers;

commit;
