-- Reconcile the roadmap with the current generic brokerage-admin foundation.
-- Authenticated production QA remains required before marking these items passed.

update public.hof_roadmap_items
set
  current_release = 'Brokerage admin controls, privacy-limited roster activity, and TXR gate foundation (2026-07-31)',
  known_issues = 'Broker-admin invite, suspension, shared-default, source-readiness, branding, and privacy boundaries are implemented and covered by automated tests. Authenticated production QA and packet/signing propagation verification remain outstanding.',
  next_action = 'Run authenticated brokerage-admin QA for authorization status, branding, shared defaults, roster visibility, and one invitation; then verify the generated packet/signing-message propagation before marking the brokerage workspace passed.',
  updated_at = now()
where slug in ('team-support', 'broker-dashboard');

-- Verification:
-- select slug, status, environment, qa_status, current_release, next_action
-- from public.hof_roadmap_items
-- where slug in ('team-support', 'broker-dashboard');
