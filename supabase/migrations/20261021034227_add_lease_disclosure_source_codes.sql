begin;
set local lock_timeout = '5s';

-- Components of the lease-listing package, not new standalone agreements.
-- Retain every existing source code and every RLS/storage/table grant.
alter table public.hof_brokerage_form_sources
  drop constraint if exists hof_brokerage_form_sources_form_code_check;
alter table public.hof_brokerage_form_sources
  add constraint hof_brokerage_form_sources_form_code_check check (form_code in (
    'TXR-1501','TXR-1506','TXR-1507','TXR-1508','TXR-1905','TXR-1914','TXR-1917','TXR-1919','TXR-1948','TXR-1953','TXR-1954',
    'TXR-1101','TXR-1102','TXR-1406','TXR-1418','TXR-2008','TXR-2015',
    'TREC-55-1','TREC-61-0','TREC-62-0','TREC-38-8','TREC-39-11'
  ));

-- Extend only the pending lease contract. Deployed release v1/v2/v3 functions
-- remain unchanged; this invoker-only probe reads catalog capabilities only.
create or replace function public.hof_lease_listing_schema_readiness()
returns jsonb language plpgsql stable security invoker set search_path=pg_catalog
as $$
declare
  baseline jsonb;
  missing text[];
  constraint_definition text;
  supported_form_code text;
begin
  baseline := public.hof_release_schema_readiness();
  select coalesce(array_agg(value),array[]::text[]) into missing
    from jsonb_array_elements_text(coalesce(baseline->'missing','[]'::jsonb)) as value;
  if baseline->>'contract' is distinct from 'homeofferflow-release-schema-v1' then
    missing := array_append(missing,'contract:release-v1');
  end if;
  if baseline->'ready' is distinct from 'true'::jsonb and cardinality(missing)=0 then
    missing := array_append(missing,'baseline:not-ready');
  end if;
  select pg_get_constraintdef(c.oid) into constraint_definition from pg_constraint c
    where c.conrelid=to_regclass('public.hof_standalone_agreements')
      and c.conname='hof_standalone_agreements_form_code_check' and c.contype='c' and c.convalidated;
  if constraint_definition is null or strpos(constraint_definition,quote_literal('TXR-1102'))=0 then
    missing := array_append(missing,'form_code:hof_standalone_agreements.TXR-1102');
  end if;
  select pg_get_constraintdef(c.oid) into constraint_definition from pg_constraint c
    where c.conrelid=to_regclass('public.hof_brokerage_form_sources')
      and c.conname='hof_brokerage_form_sources_form_code_check' and c.contype='c' and c.convalidated;
  foreach supported_form_code in array array['TXR-2008','TXR-2015'] loop
    if constraint_definition is null or strpos(constraint_definition,quote_literal(supported_form_code))=0 then
      missing := array_append(missing,'form_code:hof_brokerage_form_sources.'||supported_form_code);
    end if;
  end loop;
  return jsonb_build_object('contract','homeofferflow-lease-listing-schema-v1',
    'ready',cardinality(missing)=0,'missing',to_jsonb(missing));
end;
$$;
revoke all on function public.hof_lease_listing_schema_readiness() from public,anon,authenticated;
grant execute on function public.hof_lease_listing_schema_readiness() to service_role;
notify pgrst,'reload schema';
commit;
