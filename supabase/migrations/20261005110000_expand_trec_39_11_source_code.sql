begin;
set local lock_timeout = '5s';

alter table public.hof_brokerage_form_sources
  drop constraint if exists hof_brokerage_form_sources_form_code_check;

alter table public.hof_brokerage_form_sources
  add constraint hof_brokerage_form_sources_form_code_check check (form_code in (
    'TXR-1501','TXR-1506','TXR-1507','TXR-1508','TXR-1905','TXR-1914','TXR-1917','TXR-1919','TXR-1948','TXR-1953','TXR-1954',
    'TXR-1101','TXR-1102','TXR-1406','TXR-1418','TREC-55-1','TREC-61-0','TREC-62-0','TREC-38-8','TREC-39-11'
  ));

commit;
