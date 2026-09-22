-- Add the current TREC 62-0 seller notice to the existing private source
-- library. Access continues to be governed by the table's existing RLS and
-- the authenticated HomeOfferFlow source-catalog API.

begin;

set local lock_timeout = '5s';

alter table public.hof_brokerage_form_sources
  drop constraint if exists hof_brokerage_form_sources_form_code_check;

alter table public.hof_brokerage_form_sources
  add constraint hof_brokerage_form_sources_form_code_check
  check (form_code in (
    'TXR-1501', 'TXR-1506', 'TXR-1507', 'TXR-1508',
    'TXR-1905', 'TXR-1914', 'TXR-1917', 'TXR-1919',
    'TXR-1948', 'TXR-1953', 'TXR-1954',
    'TXR-1101', 'TXR-1102', 'TXR-1406', 'TXR-1418',
    'TREC-55-1', 'TREC-61-0', 'TREC-62-0'
  ));

commit;

-- Verification after applying:
-- select pg_get_constraintdef(oid)
-- from pg_constraint
-- where conrelid = 'public.hof_brokerage_form_sources'::regclass
--   and conname = 'hof_brokerage_form_sources_form_code_check';
