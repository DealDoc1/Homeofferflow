
begin;
set local lock_timeout = '5s';

-- Preserve all released forms. TXR-1102 is source-only, not implemented yet.
alter table public.hof_standalone_agreements
  drop constraint if exists hof_standalone_agreements_form_code_check;
alter table public.hof_standalone_agreements
  add constraint hof_standalone_agreements_form_code_check check (form_code in (
    'TXR-1101','TXR-1501','TXR-1506','TXR-1507','TXR-1508','TXR-1905','TXR-1914','TXR-1917','TXR-1919','TXR-1948','TXR-1953','TXR-1954','TREC-62-0','TREC-38-8','TREC-39-11'
  ));

-- Same service-only readiness contract, now covering the new persisted code.
create or replace function public.hof_release_schema_readiness()
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  missing text[] := array[]::text[];
  protected_table text;
  form_code_definition text;
  supported_form_code text;
begin
  if pg_catalog.to_regclass('public.hof_agent_profile_aliases') is null then
    missing := pg_catalog.array_append(missing, 'table:hof_agent_profile_aliases');
  end if;
  if pg_catalog.to_regclass('public.hof_email_deliveries') is null then
    missing := pg_catalog.array_append(missing, 'table:hof_email_deliveries');
  end if;
  if pg_catalog.to_regclass('public.hof_packet_generations') is null then
    missing := pg_catalog.array_append(missing, 'table:hof_packet_generations');
  end if;
  if pg_catalog.to_regclass('public.hof_checkout_payloads') is null then
    missing := pg_catalog.array_append(missing, 'table:hof_checkout_payloads');
  end if;
  if not exists (
    select 1 from information_schema.columns where table_schema = 'public'
      and table_name = 'hof_usage_events' and column_name = 'generation_key'
  ) then
    missing := pg_catalog.array_append(missing, 'column:hof_usage_events.generation_key');
  end if;
  if pg_catalog.to_regprocedure('public.hof_claim_packet_generation(uuid,uuid,text,uuid)') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_claim_packet_generation');
  end if;
  if pg_catalog.to_regprocedure('public.hof_complete_packet_generation(uuid,text,uuid)') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_complete_packet_generation');
  end if;
  if pg_catalog.to_regprocedure('public.hof_release_unrendered_packet(uuid,text,uuid)') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_release_unrendered_packet');
  end if;
  if pg_catalog.to_regprocedure('public.hof_packet_usage_summary(uuid)') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_packet_usage_summary');
  end if;
  if pg_catalog.to_regprocedure('public.hof_preserve_email_delivery()') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_preserve_email_delivery');
  end if;
  if pg_catalog.to_regprocedure('public.hof_protect_offer_packet_autosave()') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_protect_offer_packet_autosave');
  end if;
  if pg_catalog.to_regprocedure('public.hof_preserve_checkout_payload()') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_preserve_checkout_payload');
  end if;
  foreach protected_table in array array[
    'hof_agent_profile_aliases', 'hof_email_deliveries', 'hof_packet_generations',
    'hof_checkout_payloads', 'hof_standalone_agreements', 'hof_brokerage_form_sources'
  ] loop
    if not exists (
      select 1 from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public' and c.relname = protected_table and c.relrowsecurity
    ) then
      missing := pg_catalog.array_append(missing, 'rls:' || protected_table);
    end if;
  end loop;
  if not exists (
    select 1 from pg_catalog.pg_trigger t
    join pg_catalog.pg_class c on c.oid = t.tgrelid
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relname = 'hof_offers'
      and t.tgname = 'hof_protect_offer_packet_autosave' and not t.tgisinternal
  ) then
    missing := pg_catalog.array_append(missing, 'trigger:hof_protect_offer_packet_autosave');
  end if;
  select pg_catalog.pg_get_constraintdef(c.oid) into form_code_definition
  from pg_catalog.pg_constraint c
  where c.conrelid = pg_catalog.to_regclass('public.hof_standalone_agreements')
    and c.conname = 'hof_standalone_agreements_form_code_check' and c.contype = 'c';
  foreach supported_form_code in array array['TXR-1101','TXR-1501','TXR-1506','TXR-1507','TXR-1508','TXR-1905','TXR-1914','TXR-1917','TXR-1919','TXR-1948','TXR-1953','TXR-1954','TREC-62-0','TREC-38-8','TREC-39-11'] loop
    if form_code_definition is null
      or pg_catalog.strpos(form_code_definition, pg_catalog.quote_literal(supported_form_code)) = 0 then
      missing := pg_catalog.array_append(missing, 'form_code:hof_standalone_agreements.' || supported_form_code);
    end if;
  end loop;
  return pg_catalog.jsonb_build_object(
    'contract', 'homeofferflow-release-schema-v2',
    'ready', coalesce(pg_catalog.array_length(missing, 1), 0) = 0,
    'missing', pg_catalog.to_jsonb(missing)
  );
end;
$$;
revoke all on function public.hof_release_schema_readiness() from public, anon, authenticated;
grant execute on function public.hof_release_schema_readiness() to service_role;
comment on function public.hof_release_schema_readiness() is
  'Service-only fail-closed contract checked immediately before the coordinated HomeOfferFlow production release.';
commit;
