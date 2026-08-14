-- The original tracker schema creates a table-level unique constraint for
-- hof_qa_runs, then a separate replay index over the same columns.  The
-- subscription lifecycle baseline likewise overlaps the pre-existing unique
-- user_id index.  Retain the canonical constraint/key and remove only the
-- unreferenced duplicate indexes so writes pay for each uniqueness check once.

drop index if exists public.hof_qa_runs_scenario_release_environment_key;
drop index if exists public.hof_subscriptions_user_id_idx;
