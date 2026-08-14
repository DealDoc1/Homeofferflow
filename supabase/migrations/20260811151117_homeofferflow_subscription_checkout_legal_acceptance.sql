-- Record the distinct standard subscription checkout acceptance surface while
-- preserving the immutable one-acceptance-per-user-and-policy invariant.

begin;

alter table public.hof_legal_acceptances
  drop constraint if exists hof_legal_acceptances_source_check;

alter table public.hof_legal_acceptances
  add constraint hof_legal_acceptances_source_check
  check (source in ('offer_wizard', 'ondemand_checkout', 'subscription_checkout'));

commit;
