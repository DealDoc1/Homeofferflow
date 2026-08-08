-- Record the first seller/listing intake catalog and its anonymized golden
-- scenarios without enabling any source-gated legal form workflow.

begin;

update public.hof_roadmap_items
set
  current_release = 'Seller/listing intake catalog and golden scenarios; TREC-55-1/TREC-61-0 unsigned preview QA verified (2026-08-07)',
  known_issues = 'Private sale and lease intake, aggregate-only brokerage counts, approved TREC-55-1/TREC-61-0 sources, and unsigned preview rendering are live. Authenticated seller review QA, signer mapping, completed-signature visual QA, and release approval remain open. Listing agreements and unsupported seller forms remain source-gated.',
  next_action = 'Run authenticated TREC-55-1 seller review previews for one and two sellers, then complete recipient/signature mapping, rendered completed-PDF QA, and completed-signature visual QA before enabling seller disclosure generation or signing.',
  updated_at = now()
where slug = 'seller-workflow';

commit;

-- Verification:
-- select slug, current_release, known_issues, next_action
-- from public.hof_roadmap_items where slug = 'seller-workflow';
