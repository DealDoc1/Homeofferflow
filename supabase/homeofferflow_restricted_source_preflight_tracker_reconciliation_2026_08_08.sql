-- Record the restricted-form QA preflight milestone without enabling signing.

update public.hof_roadmap_items
set current_release = '04b514c restricted-form source preflight (2026-08-08)',
    known_issues = 'Approved and attested source records are present, but authenticated preview, signer-plan review, completed rendered-PDF QA, and completed-signature QA remain incomplete.',
    next_action = 'Run the authenticated one- and two-client preview matrix through the source preflight, then review rendered previews and complete the separate signed-PDF visual QA gate for each form.',
    updated_at = now()
where slug in (
  'txr-1501-long-buyer-tenant-representation',
  'txr-1506-general-information-notice',
  'txr-1507-short-buyer-tenant-representation',
  'txr-1508-unrepresented-showing'
);

-- Verification:
-- select slug, current_release, known_issues, next_action
-- from public.hof_roadmap_items
-- where slug like 'txr-150%';
