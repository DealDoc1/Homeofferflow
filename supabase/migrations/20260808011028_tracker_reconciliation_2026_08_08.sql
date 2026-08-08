-- Reconcile the roadmap tracker after the verified 2026-08-08 production release.
-- Metadata only: this does not change form mappings, source PDFs, signer plans,
-- billing behavior, or offer-generation behavior.

update public.hof_roadmap_items
set
  current_release = '3abba8d [deploy-production] Bundle verified HomeOfferFlow release',
  next_action = 'Continue authenticated brokerage-admin QA and restricted-form preview gates; keep legal-form signing disabled until completed visual QA is recorded.',
  updated_at = now()
where priority in (10, 14, 15);

update public.hof_roadmap_items
set
  current_release = '3abba8d [deploy-production] Bundle verified HomeOfferFlow release',
  next_action = 'Maintain locked coordinates and monitor production regressions after the verified release.',
  updated_at = now()
where priority in (27, 28, 29);

