begin;
set local lock_timeout = '5s';

-- Private source registration only. Customer standalone codes, data, RLS,
-- storage policies and table grants are deliberately unchanged.
alter table public.hof_brokerage_form_sources
  drop constraint if exists hof_brokerage_form_sources_form_code_check;
alter table public.hof_brokerage_form_sources
  add constraint hof_brokerage_form_sources_form_code_check check (form_code in (
    'TXR-1501','TXR-1506','TXR-1507','TXR-1508','TXR-1905','TXR-1914','TXR-1917','TXR-1919','TXR-1948','TXR-1953','TXR-1954',
    'TXR-1101','TXR-1102','TXR-1406','TXR-1418','TXR-2008','TXR-2015',
    'TREC-55-1','TREC-61-0','TREC-62-0','TREC-38-8','TREC-39-11'
  ));

create function public.hof_rental_source_schema_readiness()
returns jsonb language plpgsql stable security invoker set search_path=pg_catalog
as $$
declare
  definition text;
  missing text[] := array[]::text[];
  code text;
begin
  select pg_get_constraintdef(c.oid) into definition from pg_constraint c
    where c.conrelid=to_regclass('public.hof_brokerage_form_sources')
      and c.conname='hof_brokerage_form_sources_form_code_check'
      and c.contype='c' and c.convalidated;
  foreach code in array array['TXR-1501','TXR-1506','TXR-1507','TXR-1508','TXR-1905','TXR-1914','TXR-1917','TXR-1919','TXR-1948','TXR-1953','TXR-1954','TXR-1101','TXR-1102','TXR-1406','TXR-1418','TXR-2008','TXR-2015','TREC-55-1','TREC-61-0','TREC-62-0','TREC-38-8','TREC-39-11'] loop
    if definition is null or strpos(definition,quote_literal(code))=0 then
      missing := array_append(missing,'source-code:'||code);
    end if;
  end loop;
  return jsonb_build_object('contract','homeofferflow-rental-source-schema-v1',
    'ready',cardinality(missing)=0,'missing',to_jsonb(missing));
end;
$$;
revoke all on function public.hof_rental_source_schema_readiness() from public,anon,authenticated;
grant execute on function public.hof_rental_source_schema_readiness() to service_role;
notify pgrst,'reload schema';
commit;
