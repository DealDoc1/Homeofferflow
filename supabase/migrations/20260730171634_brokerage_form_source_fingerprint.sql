-- Bind every future private source-form approval to the exact PDF uploaded.
-- Existing historical source records may remain null until their source owner
-- re-uploads and re-attests to the PDF. New browser uploads calculate SHA-256
-- before storage upload and persist it with the approval record.

begin;

alter table public.hof_brokerage_form_sources
  add column if not exists source_sha256 text;

alter table public.hof_brokerage_form_sources
  drop constraint if exists hof_brokerage_form_sources_source_sha256_format_check;

alter table public.hof_brokerage_form_sources
  add constraint hof_brokerage_form_sources_source_sha256_format_check
  check (source_sha256 is null or source_sha256 ~ '^[0-9a-f]{64}$');

comment on column public.hof_brokerage_form_sources.source_sha256 is
  'SHA-256 fingerprint calculated in the administrator browser for the exact private source PDF. It is a source-identity record, not a public file locator.';

commit;

