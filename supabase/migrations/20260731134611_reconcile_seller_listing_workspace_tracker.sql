-- Reconcile the roadmap tracker with the production seller/listing intake
-- foundation. This does not enable seller-side legal-form generation.

begin;

update public.hof_roadmap_items
set
  status = 'in_progress',
  environment = 'production',
  qa_status = 'partial',
  current_release = 'Seller/listing workspace foundation (2026-07-31)',
  known_issues = 'Agent-private sale/lease intake and aggregate-only brokerage counts are live. Listing agreements, seller disclosures, packet generation, checkout, and signing remain source-gated and are not created by workspace intake.',
  next_action = 'Define the first agent-led seller packet catalog and two anonymized golden seller scenarios; obtain authorized sources, signer plans, rendered-PDF QA, and release approval before enabling any seller form.',
  updated_at = now()
where slug = 'seller-workflow';

commit;

