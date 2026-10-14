-- Operational notes only: two independently inspected roadmap records.
-- Run after canonical verification of PRs #1330 and #1333.
-- No schema, grants, account roles, billing, customer or source-vault writes.
update public.hof_roadmap_items as item
set current_release = evidence.current_release,
    known_issues = evidence.known_issues,
    next_action = evidence.next_action,
    metadata = coalesce(item.metadata, '{}'::jsonb) || evidence.snapshot,
    updated_at = now()
from (values
  (
    '56d51351-422f-4d27-88f7-54cd8ba3734c'::uuid,
    'seller-workflow',
    'PR #925 / ef2a8a8 / Vercel dpl_E1RiQrccExmNrsMRu3kag6uftJaa (2026-08-24)',
    'PR #1330 / 83241c3 / listing-to-disclosure handoff and mobile field sizing (2026-10-13)',
    'Agent-private seller leads and sale/lease listing workspaces are live with owner-only reads and aggregate brokerage reporting. Seller disclosure preparation, review and signature-request workflows are implemented; integrated completed-signature QA remains incomplete. Sale listings carry property and seller names into disclosure preparation without silently replacing current work. Source-specific sale-listing and lease-listing agreement workflows are not yet implemented; the shared catalog has no TXR-1101 or TXR-1102 entry. This is unfinished implementation, not a brokerage-seat or per-agent approval requirement.',
    'Finish integrated seller-disclosure signing QA and implement source-specific sale/lease listing agreements with accurate field and recipient mapping. Continue qualified organic acquisition into the free seller plan; keep pricing unchanged until real demand supports a redesign.',
    '{"verified_listing_disclosure_handoff_2026_10_14":{"pr":1330,"production_commit":"83241c3","evidence":"docs/release-evidence/listing-disclosure-handoff-2026-10-13.md","handoff":"production_verified","integrated_completed_signing":"not_verified","listing_agreement_implementation":"not_complete"}}'::jsonb
  ),
  (
    'e603b953-3b83-4041-a873-6a9415244cbe'::uuid,
    'brokerage-branding',
    'Broker-admin branding Storage upload and branding update flow are production implemented; authenticated propagation QA remains to be recorded (2026-08-24)',
    'PR #1333 / 4fe45d0 / accurate signing progress and stable account navigation (2026-10-14)',
    'Broker-admin branding, shared defaults, roster and invitation tools are production implemented. Sent, partial and completed offer reporting is corrected; immediate Agent Account to Brokerage navigation is production verified with active OnDemand agent membership. This session does not expose broker-admin controls. Live broker-admin branding/defaults/roster/invitation propagation and a fresh end-to-end agent activation still need their own verification; an agent view does not prove the full brokerage launch.',
    'Use an authenticated OnDemand broker-admin session to exercise branding, shared title defaults, roster visibility, invitations and one end-to-end agent activation. Preserve the current $0 today, card-required 60-day trial and $29/month renewal terms. Prepare distribution to the entire intended brokerage roster after those launch checks; do not send brokerage outreach without owner review of its draft.',
    '{"verified_brokerage_progress_2026_10_14":{"pr":1333,"production_commit":"4fe45d0850e7c072a16f0d9fdab0dd829e165fe4","deployment":"dpl_j3Yp7492NRqXJt1EM4BEHtGU57qe","evidence":"docs/release-evidence/brokerage-signing-progress-2026-10-14.md","agent_navigation":"production_verified","broker_admin_onboarding":"not_verified","roles_changed":false}}'::jsonb
  )
) as evidence(id, slug, previous_release, current_release, known_issues, next_action, snapshot)
where item.id = evidence.id
  and item.slug = evidence.slug
  and item.status = 'in_progress'
  and item.qa_status = 'partial'
  and item.current_release in (evidence.previous_release, evidence.current_release)
returning item.id, item.slug, item.status, item.qa_status,
          item.current_release, item.known_issues, item.next_action;

-- Independently read both exact IDs after execution. Zero affected rows means
-- the expected record changed: inspect it, do not remove the guard or mark QA passed.
