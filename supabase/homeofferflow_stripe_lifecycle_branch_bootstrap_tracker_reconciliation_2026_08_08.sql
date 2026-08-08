-- Record the current isolation prerequisite without changing Stripe or
-- subscription state. The lifecycle matrix remains open until an isolated
-- Supabase branch can bootstrap successfully.

update public.hof_roadmap_items
set
  known_issues = 'The production webhook guard and automated lifecycle suite are green, but two approved-cost Supabase branch attempts failed during migration bootstrap and were deleted. No Stripe test endpoint was created.',
  next_action = 'Restore a complete ordered Supabase migration chain/configuration in the repository, run branch preflight, then create one healthy isolated branch before any Stripe test endpoint or lifecycle delivery.',
  updated_at = now()
where slug = 'subscription-usage-management';
