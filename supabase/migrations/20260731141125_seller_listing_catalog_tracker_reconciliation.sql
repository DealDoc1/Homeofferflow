-- Record the first seller/listing intake catalog and its anonymized golden scenarios without enabling any source-gated legal form workflow.
begin;
update public.hof_roadmap_items
set
  current_release = 'Seller/listing intake catalog and golden scenarios (2026-07-31)',
  known_issues = 'Private sale and lease intake, aggregate-only brokerage counts, and source-readiness checks are live. Two anonymized intake scenarios now define the QA contract. Listing agreements, seller disclosures, packet generation, checkout, and signing remain source-gated.',
  next_action = 'Obtain authorized sources for the first requested seller/listing workflow, define its document-specific signer plan and field map, then complete rendered completed-PDF QA and release approval before enabling generation or signing.',
  updated_at = now()
where slug = 'seller-workflow';
commit;

