-- A service-only, read-only release contract for the coordinated application
-- and database deployment. The function is intentionally created after every
-- dependency migration so an interrupted migration run cannot report ready.
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
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'hof_usage_events'
      and column_name = 'generation_key'
  ) then
    missing := pg_catalog.array_append(missing, 'column:hof_usage_events.generation_key');
  end if;

  if pg_catalog.to_regprocedure(
    'public.hof_claim_packet_generation(uuid,uuid,text,uuid)'
  ) is null then
    missing := pg_catalog.array_append(missing, 'function:hof_claim_packet_generation');
  end if;
  if pg_catalog.to_regprocedure(
    'public.hof_complete_packet_generation(uuid,text,uuid)'
  ) is null then
    missing := pg_catalog.array_append(missing, 'function:hof_complete_packet_generation');
  end if;
  if pg_catalog.to_regprocedure(
    'public.hof_release_unrendered_packet(uuid,text,uuid)'
  ) is null then
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
    'hof_agent_profile_aliases',
    'hof_email_deliveries',
    'hof_packet_generations',
    'hof_checkout_payloads'
  ] loop
    if not exists (
      select 1
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public'
        and c.relname = protected_table
        and c.relrowsecurity
    ) then
      missing := pg_catalog.array_append(missing, 'rls:' || protected_table);
    end if;
  end loop;

  if not exists (
    select 1
    from pg_catalog.pg_trigger t
    join pg_catalog.pg_class c on c.oid = t.tgrelid
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname = 'hof_offers'
      and t.tgname = 'hof_protect_offer_packet_autosave'
      and not t.tgisinternal
  ) then
    missing := pg_catalog.array_append(missing, 'trigger:hof_protect_offer_packet_autosave');
  end if;

  return pg_catalog.jsonb_build_object(
    'contract', 'homeofferflow-release-schema-v1',
    'ready', pg_catalog.coalesce(pg_catalog.array_length(missing, 1), 0) = 0,
    'missing', pg_catalog.to_jsonb(missing)
  );
end;
$$;

revoke all on function public.hof_release_schema_readiness() from public, anon, authenticated;
grant execute on function public.hof_release_schema_readiness() to service_role;

comment on function public.hof_release_schema_readiness() is
  'Service-only fail-closed contract checked immediately before the coordinated HomeOfferFlow production release.';
