-- Operational roadmap reconciliation only. Apply after PR #1330 is verified
-- on the canonical production domain. No form, policy or billing activation.
begin;

update public.hof_roadmap_items
set current_release = 'PR #1330 / 83241c3 / listing-to-disclosure handoff and mobile field sizing (2026-10-13)',
    known_issues = 'Agent-private seller leads and sale/lease listing workspaces are live with owner-only reads and aggregate brokerage reporting. Seller disclosure preparation, review and signature-request workflows are implemented; the integrated completed-signature QA matrix remains incomplete. Sale listings now carry property and seller names into disclosure preparation without replacing current work silently. Source-specific sale-listing and lease-listing agreement workflows are not yet implemented; the approved shared catalog currently has no TXR-1101 or TXR-1102 entry. This is unfinished implementation, not a brokerage-seat or per-agent approval requirement.',
    next_action = 'Complete integrated seller-disclosure review/signing QA and implement source-specific sale/lease listing agreements with appropriate field and recipient mapping. Continue qualified organic acquisition into the free seller plan; preserve pricing until real demand supports a redesign.',
    updated_at = now()
where id = '56d51351-422f-4d27-88f7-54cd8ba3734c'
  and slug = 'seller-workflow';

commit;

-- Read back this exact row independently. Keep status=in_progress and
-- qa_status=partial; a frontend handoff does not complete the broader scope.
select id, slug, status, environment, qa_status, current_release,
       known_issues, next_action
from public.hof_roadmap_items
where id = '56d51351-422f-4d27-88f7-54cd8ba3734c'
  and slug = 'seller-workflow';
