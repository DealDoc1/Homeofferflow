-- Keep the live product tracker aligned with the Stripe lifecycle protections
-- shipped through the release branch. This is tracker data only; it does not
-- alter Stripe, subscription rows, checkout behavior, or webhook processing.

update public.hof_roadmap_items
set
  current_release = '77e787b brokerage billing suspension reason hardening',
  known_issues = 'Stripe lifecycle guardrails are covered by the automated suite and the suspension_reason schema is live. The webhook code change is pushed but still requires the next intentional Vercel production deployment. A real Stripe Sandbox lifecycle must remain isolated from the production webhook endpoint.',
  next_action = 'Bundle 77e787b into the next intentional production deployment, then verify manual broker suspension, billing suspension, renewal recovery, and removed-seat protection against live webhook delivery metadata through a dedicated nonproduction Stripe endpoint. never connect Stripe test-mode events to production.',
  updated_at = now()
where slug = 'subscription-usage-management';

-- Verification:
-- select slug, status, qa_status, current_release, known_issues, next_action
-- from public.hof_roadmap_items
-- where slug = 'subscription-usage-management';
