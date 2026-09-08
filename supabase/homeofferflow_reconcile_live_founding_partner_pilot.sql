-- Reconcile the founding-partner pilot with its released production lifecycle.
-- This tracker update does not create a charge, placement, agreement, or
-- public directory listing.

begin;

update public.hof_roadmap_items
set
  status = 'in_progress',
  environment = 'production',
  qa_status = 'partial',
  current_release = 'live partner application, Stripe checkout, secure onboarding, and SignWell agreement lifecycle (2026-09-07)',
  known_issues = 'The public partner application, payment return, secure onboarding, executed-agreement tracking, and controlled directory activation are live. There are no paid partner placements activated yet, so live commercial conversion and directory-placement measurement remain unproven.',
  next_action = 'Qualify and onboard the first paid partner, then verify its agreement-confirmed directory activation and aggregate impression/click reporting.'
where slug = 'founding-partner-pilot';

commit;
