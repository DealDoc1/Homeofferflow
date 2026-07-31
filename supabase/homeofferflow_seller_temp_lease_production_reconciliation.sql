-- Reconcile the roadmap after the completed four-party staging packet and
-- production SignWell recipient-order gate were released in 20-19.
--
-- This changes tracker state only. It does not alter form coordinates, source
-- files, signer routing, or packet generation behavior.

begin;

update public.hof_roadmap_items
set
  status = 'production',
  environment = 'production',
  qa_status = 'passed',
  target_release = null,
  current_release = '08272d6 Release seller temporary lease execution',
  known_issues = null,
  next_action = 'Run the seller-temporary-lease scenario in the golden regression suite after any packet, signer, or production API change.',
  is_locked = true,
  updated_at = now()
where slug = 'seller-temporary-lease';

update public.hof_roadmap_items
set
  status = 'production',
  environment = 'production',
  qa_status = 'passed',
  current_release = '08272d6 Release seller temporary lease execution',
  known_issues = null,
  next_action = 'Retain four-party seller temporary lease SignWell recipient-order coverage in every production release.',
  updated_at = now()
where slug = 'target-seller-temporary-lease';

commit;

-- Verification:
-- select slug, status, environment, qa_status, current_release, next_action
-- from public.hof_roadmap_items
-- where slug in ('seller-temporary-lease', 'target-seller-temporary-lease');
