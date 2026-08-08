-- Allows a brokerage administrator to retain authorized listing-side source
-- PDFs privately. This does not enable form completion, signature, delivery,
-- or source download by agents.

begin;

alter table public.hof_brokerage_form_sources
  drop constraint if exists hof_brokerage_form_sources_form_code_check;

alter table public.hof_brokerage_form_sources
  add constraint hof_brokerage_form_sources_form_code_check
  check (form_code in (
    'TXR-1501', 'TXR-1506', 'TXR-1507', 'TXR-1508',
    'TXR-1101', 'TXR-1102', 'TXR-1406', 'TXR-1418'
  ));

commit;

