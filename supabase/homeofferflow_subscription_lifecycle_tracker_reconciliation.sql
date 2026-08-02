-- Keep the live product tracker aligned with the Stripe lifecycle protections
-- shipped through the release branch. This is tracker data only; it does not
-- alter Stripe, subscription rows, checkout behavior, or webhook processing.

update public.hof_roadmap_items
set
  current_release = '51feaeb staged agent billing access hardening',
  known_issues = 'Native 60-day card-required trial checkout and production webhook handling are live. Automated coverage includes trial invoices, renewal dispatch, failed payments, completed cancellations, scheduled cancellations, and suspension of existing agent brokerage memberships when billing becomes past_due or canceled. The hardening commit is staged and must be deployed in the next intentional production release. A real Stripe Sandbox lifecycle must remain isolated from the production webhook endpoint.',
  next_action = 'Bundle 51feaeb into the next intentional production deployment, then monitor live webhook deliveries. Run renewal, failed-payment, and cancellation simulations only through a dedicated nonproduction Stripe endpoint or legitimate account lifecycle; never connect Stripe test-mode events to production.',
  updated_at = now()
where slug = 'subscription-usage-management';

-- Verification:
-- select slug, status, qa_status, current_release, known_issues, next_action
-- from public.hof_roadmap_items
-- where slug = 'subscription-usage-management';
