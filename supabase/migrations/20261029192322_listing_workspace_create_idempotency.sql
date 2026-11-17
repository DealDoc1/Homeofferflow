-- Preserve keyed listing workspace saves across ambiguous responses.
begin;
set local lock_timeout = '5s';

alter table public.hof_listing_workspaces
  add column if not exists client_request_id uuid;

create unique index if not exists hof_listing_workspaces_agent_request_idx
  on public.hof_listing_workspaces (agent_user_id, client_request_id)
  where client_request_id is not null;

create or replace function public.hof_listing_workspace_creation_schema_ready()
returns boolean
language sql
stable
set search_path = pg_catalog
as $$
  select exists (
    select 1 from pg_attribute
    where attrelid = 'public.hof_listing_workspaces'::regclass
      and attname = 'client_request_id' and atttypid = 'uuid'::regtype
      and not attisdropped and not attnotnull
  ) and exists (
    select 1 from pg_index i
    where i.indrelid = 'public.hof_listing_workspaces'::regclass
      and i.indexrelid = to_regclass('public.hof_listing_workspaces_agent_request_idx')
      and i.indisunique and i.indisvalid and i.indisready and i.indnkeyatts = 2
      and pg_get_indexdef(i.indexrelid, 1, true) = 'agent_user_id'
      and pg_get_indexdef(i.indexrelid, 2, true) = 'client_request_id'
      and pg_get_expr(i.indpred, i.indrelid) = '(client_request_id IS NOT NULL)'
  );
$$;

revoke all on function public.hof_listing_workspace_creation_schema_ready() from public, anon, authenticated;
grant execute on function public.hof_listing_workspace_creation_schema_ready() to service_role;

commit;
