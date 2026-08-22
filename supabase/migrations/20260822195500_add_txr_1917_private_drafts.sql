begin;

alter table public.hof_standalone_agreements
  drop constraint if exists hof_standalone_agreements_form_code_check;

alter table public.hof_standalone_agreements
  add constraint hof_standalone_agreements_form_code_check
  check (form_code in ('TXR-1501', 'TXR-1506', 'TXR-1507', 'TXR-1508', 'TXR-1905', 'TXR-1914', 'TXR-1917', 'TXR-1919'));

commit;
