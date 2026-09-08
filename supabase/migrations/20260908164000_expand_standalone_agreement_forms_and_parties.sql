begin;

alter table public.hof_standalone_agreements
  drop constraint if exists hof_standalone_agreements_form_code_check;

alter table public.hof_standalone_agreements
  add constraint hof_standalone_agreements_form_code_check
  check (form_code in (
    'TXR-1501', 'TXR-1506', 'TXR-1507', 'TXR-1508',
    'TXR-1905', 'TXR-1914', 'TXR-1917', 'TXR-1919',
    'TXR-1948', 'TXR-1953', 'TXR-1954'
  ));

alter table public.hof_standalone_agreements
  drop constraint if exists hof_standalone_agreements_client_names_check;

alter table public.hof_standalone_agreements
  add constraint hof_standalone_agreements_client_names_check
  check (
    jsonb_typeof(client_names) = 'array'
    and jsonb_array_length(client_names) between 1 and 4
  );

commit;
