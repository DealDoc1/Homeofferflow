-- Consolidate duplicate legacy public offer policies. Current browser offer
-- drafts run only after sign-in and use the authenticated owner policies.
-- Service-role packet generation is unaffected.

begin;

drop policy if exists "users can insert own offers" on public.hof_offers;
drop policy if exists "hof_offers own read" on public.hof_offers;
drop policy if exists "users can view own offers" on public.hof_offers;
drop policy if exists "hof_offers own update" on public.hof_offers;
drop policy if exists "users can update own offers" on public.hof_offers;

commit;
