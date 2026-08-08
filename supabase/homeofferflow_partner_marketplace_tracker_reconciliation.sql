-- Keep the live roadmap aligned with the paid-partner activation and privacy
-- gate released on 2026-07-29. This is tracker data only; it does not change
-- Stripe, public placement records, or partner subscriptions.

update public.hof_roadmap_items
set
  current_release = 'Paid partner placement activation and privacy gate (2026-07-29); renewal terms reconciled (2026-08-03); lifecycle reporting and directory attribution instrumentation (2026-08-08)',
  known_issues = 'Paid partner applications and agreement-confirmed placement activation are live. The public directory exposes only curated placement fields and records session-deduplicated impressions plus outbound-click attribution events. The admin view now reports launch-period and renewal-review operations from activation timestamps. Checkout is authoritative for commercial billing: the launch charge is collected at checkout, the recurring plan begins after the 90-day trial, and it renews monthly unless canceled. Placement-specific scope and inventory still require a written agreement before activation.',
  next_action = 'Confirm one paid partner application against the written placement agreement, activate it through the controlled workflow, and verify the curated public directory display plus impression/click events.',
  updated_at = now()
where slug = 'partner-marketplace';
