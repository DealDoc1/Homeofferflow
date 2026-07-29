-- Reconcile the roadmap summary with the fail-closed production adapter.
--
-- TREC 15-7 Seller's Temporary Residential Lease has a staging packet and
-- documented staging QA, but api/fill_pdf_20_19_production_adapter.py still
-- rejects this path. The tracker must not advertise it as production until the
-- completed signed-PDF release gate and production verification are approved.

begin;

update public.hof_roadmap_items
set
  status = 'staging_passed',
  environment = 'staging',
  qa_status = 'passed',
  target_release = 'Next production unlock',
  current_release = 'agent/seller-temp-lease-staging',
  known_issues = 'Production adapter still blocks this path until the completed signed-PDF release gate is approved.',
  next_action = 'Complete the documented signed staging packet review, then create a production unlock PR and verify the production packet.',
  is_locked = true
where slug = 'seller-temporary-lease';

commit;
