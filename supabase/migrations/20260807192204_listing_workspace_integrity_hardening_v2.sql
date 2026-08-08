-- Seller/listing workspace integrity hardening.
--
-- This migration does not activate or sign a legal form. It constrains the
-- private intake workspace so the browser can only record known workflow
-- requests and keeps updated_at reliable for agent and broker summaries.

begin;

create or replace function public.hof_listing_workflows_allowed(value jsonb)
returns boolean
language plpgsql
immutable
set search_path = public
as $$
declare
  item text;
begin
  if jsonb_typeof(value) <> 'array' then
    return false;
  end if;
  for item in select jsonb_array_elements_text(value) loop
    if item not in ('listing_agreement', 'seller_disclosure', 'lease_listing') then
      return false;
    end if;
  end loop;
  return true;
end;
$$;

alter table public.hof_listing_workspaces
  drop constraint if exists hof_listing_workspaces_requested_workflows_allowed;

alter table public.hof_listing_workspaces
  add constraint hof_listing_workspaces_requested_workflows_allowed
  check (public.hof_listing_workflows_allowed(requested_workflows));

create or replace function public.hof_touch_listing_workspace_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists hof_listing_workspaces_touch_updated_at
  on public.hof_listing_workspaces;

create trigger hof_listing_workspaces_touch_updated_at
before update on public.hof_listing_workspaces
for each row execute function public.hof_touch_listing_workspace_updated_at();

revoke all on function public.hof_touch_listing_workspace_updated_at() from public;
revoke all on function public.hof_listing_workflows_allowed(jsonb) from public;

commit;



