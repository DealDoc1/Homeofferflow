-- Seller/listing workspace integrity hardening.
--
-- This migration does not activate or sign a legal form. It constrains the
-- private intake workspace so the browser can only record known workflow
-- requests and keeps updated_at reliable for agent and broker summaries.

begin;

alter table public.hof_listing_workspaces
  drop constraint if exists hof_listing_workspaces_requested_workflows_allowed;

alter table public.hof_listing_workspaces
  add constraint hof_listing_workspaces_requested_workflows_allowed
  check (
    jsonb_typeof(requested_workflows) = 'array'
    and not exists (
      select 1
      from jsonb_array_elements_text(requested_workflows) as requested(value)
      where requested.value not in (
        'listing_agreement',
        'seller_disclosure',
        'lease_listing'
      )
    )
  );

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

commit;

