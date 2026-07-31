-- Reconcile the roadmap summary with the production TREC 15-7 release.
--
-- The seller temporary lease passed the documented staging packet and
-- completed-signature review, then received the production execution release.
-- Keep the tracker explicit about the required buyer/landlord and
-- seller/tenant signing order and the ongoing regression obligation.

begin;

update public.hof_roadmap_items
set
  status = 'production',
  environment = 'production',
  qa_status = 'passed',
  target_release = 'Production',
  current_release = 'Seller temporary lease production release (2026-07-29)',
  known_issues = null,
  next_action = 'Production Seller Temporary Residential Lease (TREC 15-7) is live with buyer/landlord and seller/tenant execution routing. Run the approved seller-lease golden regression after every packet assembly or signature-placement change.',
  is_locked = true
where slug = 'seller-temporary-lease';

commit;
