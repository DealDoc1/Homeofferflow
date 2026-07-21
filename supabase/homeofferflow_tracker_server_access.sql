-- Keep the product/QA tracker behind the validated Admin Dashboard API.
-- The browser never receives direct table privileges; the server uses service_role.

revoke all on table
  public.hof_platform_admins,
  public.hof_roadmap_items,
  public.hof_qa_scenarios,
  public.hof_qa_runs,
  public.hof_qa_results,
  public.hof_releases
from anon, authenticated;

grant all on table
  public.hof_platform_admins,
  public.hof_roadmap_items,
  public.hof_qa_scenarios,
  public.hof_qa_runs,
  public.hof_qa_results,
  public.hof_releases
to service_role;

drop policy if exists "platform_admins_read_self" on public.hof_platform_admins;
drop policy if exists "roadmap_admin_all" on public.hof_roadmap_items;
drop policy if exists "qa_scenarios_admin_all" on public.hof_qa_scenarios;
drop policy if exists "qa_runs_admin_all" on public.hof_qa_runs;
drop policy if exists "qa_results_admin_all" on public.hof_qa_results;
drop policy if exists "releases_admin_all" on public.hof_releases;

create policy "platform_admins_server_only" on public.hof_platform_admins
for all to authenticated using (false) with check (false);
create policy "roadmap_server_only" on public.hof_roadmap_items
for all to authenticated using (false) with check (false);
create policy "qa_scenarios_server_only" on public.hof_qa_scenarios
for all to authenticated using (false) with check (false);
create policy "qa_runs_server_only" on public.hof_qa_runs
for all to authenticated using (false) with check (false);
create policy "qa_results_server_only" on public.hof_qa_results
for all to authenticated using (false) with check (false);
create policy "releases_server_only" on public.hof_releases
for all to authenticated using (false) with check (false);

create index if not exists hof_qa_runs_release_id_idx
  on public.hof_qa_runs(release_id);
create index if not exists hof_qa_runs_executed_by_idx
  on public.hof_qa_runs(executed_by);
