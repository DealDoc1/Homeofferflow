-- Adds TXR-1508 as a separately tracked, private source-gated agreement draft.
-- This never stores the member form itself and does not enable PDF delivery.

begin;

alter table public.hof_standalone_agreements
  drop constraint if exists hof_standalone_agreements_form_code_check;

alter table public.hof_standalone_agreements
  add constraint hof_standalone_agreements_form_code_check
  check (form_code in ('TXR-1501', 'TXR-1507', 'TXR-1508'));

commit;

