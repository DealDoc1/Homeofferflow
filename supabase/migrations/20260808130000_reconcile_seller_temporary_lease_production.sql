-- Keep the source-of-truth tracker aligned with the verified production
-- Seller Temporary Residential Lease release.
-- Metadata only: no form mappings, source PDFs, signer geometry, or packet
-- generation behavior is changed.

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

update public.hof_qa_scenarios
set
  current_status = 'production',
  last_verified_release = '08272d6 Release seller temporary lease execution',
  notes = 'Four-party seller temporary lease SignWell recipient-order coverage is included in every production release.',
  updated_at = now()
where scenario_key = 'target-seller-temporary-lease';

update public.hof_releases
set
  environment = 'production',
  status = 'deployed',
  qa_status = 'passed',
  git_branch = 'main',
  commit_sha = '08272d6',
  summary = 'TREC 15-7 completed four-party packet passed field-by-field and completed-signature visual review; production recipient-order routing is enabled.',
  known_issues = null,
  next_action = 'Retain the seller-temporary-lease scenario in every production regression run.',
  approved_by = 'Andrew Christian',
  approved_at = coalesce(approved_at, now()),
  deployed_at = coalesce(deployed_at, now()),
  updated_at = now()
where release_key = 'seller-temporary-lease-unlock';
