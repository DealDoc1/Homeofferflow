-- Reconcile the Stripe lifecycle roadmap item after the verified production
-- release that contains the brokerage billing-suspension protections.
-- Tracker metadata only: no Stripe, subscription, membership, or webhook rows
-- are changed by this statement.

update public.hof_roadmap_items
set
  current_release = '3abba8d verified production release (billing lifecycle protections included)',
  known_issues = 'Stripe lifecycle guardrails are deployed and covered by the automated suite. A dedicated nonproduction Stripe lifecycle run remains required for live event-delivery verification; never connect Stripe test-mode events to the production webhook endpoint.',
  next_action = 'Run the isolated nonproduction Stripe lifecycle matrix for manual broker suspension, billing suspension, renewal recovery, and removed-seat protection. Keep test-mode events isolated from production.',
  updated_at = now()
where slug = 'subscription-usage-management';

-- Verification:
-- select slug, status, qa_status, current_release, known_issues, next_action
-- from public.hof_roadmap_items
-- where slug = 'subscription-usage-management';
