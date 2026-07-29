-- Keep the live product tracker aligned with the Stripe lifecycle protections
-- shipped through PR #40. This is tracker data only; it does not alter Stripe,
-- subscription rows, checkout behavior, or webhook processing.

update public.hof_roadmap_items
set
  current_release = 'PR #40 scheduled cancellation lifecycle QA',
  known_issues = 'Native 60-day card-required trial checkout and production webhook handling are live. Automated coverage now includes trial invoices, renewal dispatch, failed payments, completed cancellations, and scheduled cancellations. A real Stripe Sandbox lifecycle must remain isolated from the production webhook endpoint.',
  next_action = 'Monitor live production webhook deliveries. Run renewal, failed-payment, and cancellation simulations only through a dedicated nonproduction Stripe endpoint or legitimate account lifecycle; never connect Stripe test-mode events to production.',
  updated_at = now()
where slug = 'subscription-usage-management';

-- Verification:
-- select slug, status, qa_status, current_release, known_issues, next_action
-- from public.hof_roadmap_items
-- where slug = 'subscription-usage-management';
