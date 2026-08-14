-- Reconcile the production tracker after the signed-packet reliability release.
-- Metadata only: this does not alter offers, customer profiles, subscriptions,
-- form mappings, Stripe configuration, or Google Places address behavior.

update public.hof_roadmap_items
set
  current_release = 'a292f25 completed SignWell-status precedence + 86363ed PWA shell v9 (2026-08-13)',
  next_action = 'Monitor production signing refreshes and the explicit installed-PWA update prompt; configure authenticated SignWell webhooks only after the provider verification material is supplied.',
  updated_at = now()
where slug = 'signwell-status-tracking';

update public.hof_roadmap_items
set
  current_release = 'a292f25 completed SignWell-status precedence + 86363ed PWA shell v9 (2026-08-13)',
  qa_status = 'passed',
  next_action = 'Use the authenticated platform-admin view for release monitoring; keep customer-account and brokerage-admin QA scoped to their respective signed-in roles.',
  updated_at = now()
where slug = 'admin-dashboard';

-- Verification:
-- select slug, status, qa_status, current_release, next_action
-- from public.hof_roadmap_items
-- where slug in ('signwell-status-tracking', 'admin-dashboard');
