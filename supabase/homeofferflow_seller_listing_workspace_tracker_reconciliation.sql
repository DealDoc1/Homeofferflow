-- Reconcile the roadmap tracker with the production seller/listing intake
-- foundation. This does not enable seller-side legal-form generation.

begin;

update public.hof_roadmap_items
set
  status = 'in_progress',
  environment = 'production',
  qa_status = 'partial',
  current_release = 'TREC-55-1/TREC-61-0 unsigned preview QA verified (2026-08-07)',
  known_issues = 'Agent-private sale/lease intake, aggregate-only brokerage counts, approved TREC-55-1/TREC-61-0 sources, and unsigned preview rendering are live. Authenticated seller review QA, document-specific signer mapping, completed-signature visual QA, and release approval remain open; listing agreements and other seller forms remain source-gated.',
  next_action = 'Run authenticated TREC-55-1 seller review previews for one and two sellers, then complete recipient/signature mapping, rendered-PDF QA, and completed-signature visual QA before enabling seller disclosure generation or signing.',
  updated_at = now()
where slug = 'seller-workflow';

commit;

-- Verification:
-- select slug, status, environment, qa_status, current_release, known_issues,
--        next_action
-- from public.hof_roadmap_items
-- where slug = 'seller-workflow';
