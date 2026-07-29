-- Adds the TXR-1501 long buyer/tenant representation agreement as a separate,
-- private draft record type. It does not activate source-PDF generation or
-- signing. TXR-1501 remains broker-authorized and source-gated.

begin;

alter table public.hof_standalone_agreements
  drop constraint if exists hof_standalone_agreements_form_code_check;

alter table public.hof_standalone_agreements
  add constraint hof_standalone_agreements_form_code_check
  check (form_code in ('TXR-1501', 'TXR-1507'));

commit;

-- Verification after applying:
-- select conname, pg_get_constraintdef(oid)
-- from pg_constraint
-- where conrelid = 'public.hof_standalone_agreements'::regclass
--   and conname = 'hof_standalone_agreements_form_code_check';
