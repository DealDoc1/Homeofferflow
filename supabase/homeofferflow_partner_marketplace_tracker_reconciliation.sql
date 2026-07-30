-- Keep the live roadmap aligned with the paid-partner activation and privacy
-- gate released on 2026-07-29. This is tracker data only; it does not change
-- Stripe, public placement records, or partner subscriptions.

update public.hof_roadmap_items
set
  current_release = 'Paid partner placement activation and privacy gate (2026-07-29)',
  known_issues = 'Paid partner applications and agreement-confirmed placement activation are live. The public directory now exposes only curated placement fields. Commercial terms still conflict: checkout starts the 90-day trial and auto-renewal, while pilot documents say placement-live start and separate written renewal.',
  next_action = 'Choose the founding-partner trial start and renewal rule, then align Stripe, checkout copy, and rate-card terms. After agreement confirmation, activate one paid partner application through the controlled placement workflow and verify public directory display.',
  updated_at = now()
where slug = 'partner-marketplace';
