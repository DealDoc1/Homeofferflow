-- Reconcile the product tracker with the completed isolated Stripe Sandbox
-- lifecycle QA. This is operational metadata only; it does not modify any
-- subscription, membership, event, or credential.

update public.hof_roadmap_items
set
  status = 'production',
  environment = 'production',
  qa_status = 'passed',
  target_release = 'Billing hardening',
  known_issues = 'Stripe lifecycle guardrails are deployed. Isolated Stripe Sandbox QA verified signed checkout, trial, cancellation, duplicate replay, payment failure, billing suspension, manual-suspension preservation, removed-seat preservation, and deletion. No test event was sent to production.',
  next_action = 'Monitor billing recovery and portal-return cohorts before changing prices, trial length, or packet limits.',
  current_release = 'Stripe lifecycle QA 2026-08-10',
  updated_at = now()
where slug = 'subscription-usage-management';

-- Verification:
-- select status, environment, qa_status, current_release
-- from public.hof_roadmap_items
-- where slug = 'subscription-usage-management';
