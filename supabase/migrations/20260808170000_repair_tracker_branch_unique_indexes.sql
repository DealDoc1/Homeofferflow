-- Repair a schema-only Supabase branch baseline that predated the tracker
-- replay fix. The production table already has the equivalent uniqueness via
-- its table constraint; CREATE UNIQUE INDEX IF NOT EXISTS is safe there and
-- gives branch baselines the conflict target required by tracker seed data.

create unique index if not exists hof_qa_runs_scenario_release_environment_key
  on public.hof_qa_runs(scenario_id, release_name, environment);
