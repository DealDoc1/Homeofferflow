begin;
revoke all on public.hof_offer_signing_parties from authenticated;
revoke all on public.hof_offer_signing_parties from anon;
commit;

