
begin;
set local lock_timeout = '5s';

-- Preserve all released forms. TXR-1102 is source-only, not implemented yet.
alter table public.hof_standalone_agreements
  drop constraint if exists hof_standalone_agreements_form_code_check;
alter table public.hof_standalone_agreements
  add constraint hof_standalone_agreements_form_code_check check (form_code in (
    'TXR-1101','TXR-1501','TXR-1506','TXR-1507','TXR-1508','TXR-1905','TXR-1914','TXR-1917','TXR-1919','TXR-1948','TXR-1953','TXR-1954','TREC-62-0','TREC-38-8','TREC-39-11'
  ));

-- Preserve the already deployed v1/v2 readiness functions. The coordinated
-- listing/disclosure binding migration adds its own additive v3 wrapper.
commit;
