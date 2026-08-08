-- Add supplied TREC seller-side source families to the private source vault.
-- This expands source intake/readiness only. It does not create a renderer,
-- signer plan, packet, or executable workflow.

begin;

alter table public.hof_brokerage_form_sources
  drop constraint if exists hof_brokerage_form_sources_form_code_check;

alter table public.hof_brokerage_form_sources
  add constraint hof_brokerage_form_sources_form_code_check
  check (form_code in (
    'TXR-1501', 'TXR-1506', 'TXR-1507', 'TXR-1508',
    'TXR-1101', 'TXR-1102', 'TXR-1406', 'TXR-1418',
    'TREC-55-1', 'TREC-61-0'
  ));

commit;



