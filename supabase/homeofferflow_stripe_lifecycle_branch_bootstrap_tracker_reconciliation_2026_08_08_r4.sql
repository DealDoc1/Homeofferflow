-- Record the fourth isolated-branch bootstrap result without changing Stripe or
-- subscription state. The lifecycle matrix remains open until a Supabase
-- branch can bootstrap successfully.

update public.hof_roadmap_items
set
  known_issues = 'The production webhook guard and automated lifecycle suite are green, and the live project exposes 61 ordered migrations. The repository now has a schema-only baseline, all ordered migration SQL, and secret-free Supabase config; local preflight passes. Four approved-cost Supabase branch attempts still failed during bootstrap and were deleted. No Stripe test endpoint was created; test-mode events remain isolated from production.',
  next_action = 'Obtain Supabase branch-service diagnostics or a documented bootstrap procedure for this project. Do not create another paid branch or Stripe test endpoint until a new diagnostic path is available and a branch is healthy with a distinct database URL.',
  updated_at = now()
where slug = 'subscription-usage-management';

-- Verification:
-- select slug, status, qa_status, current_release, known_issues, next_action
-- from public.hof_roadmap_items
-- where slug = 'subscription-usage-management';
