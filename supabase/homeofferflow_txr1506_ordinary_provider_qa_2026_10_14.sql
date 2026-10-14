-- Record one recovered completed-provider case; no customer-map activation.
-- Execute only after the read-only immutable PDF audit and six-page visual review.
update public.hof_roadmap_items
set known_issues = 'The corrected workflow is production-live. Historical single-signer review exists. The ordinary two-consumer/associate completed-provider component now passes current-map comparison and all-six-page visual review: 10 initials, 3 signatures and 3 dates. Broker-role and long/Unicode continuation cases remain unverified; this is not a pass for the whole form matrix.',
    next_action = 'Complete only the missing broker-role and long/Unicode continuation provider cases, including appended-page initials. Reuse the covered ordinary two-consumer/associate result instead of resending it. Preserve all historical packets and the current customer map.',
    metadata = coalesce(metadata, '{}'::jsonb) || '{"completed_provider_case_2026_10_14":{"case":"ordinary_two_consumers_and_associate","provider_document_id":"13f7fe33-3620-4b61-b66e-4c96b5792c1f","completed_sha256":"d5dd3d701b06cff87934235680dbee1d40e56fe99d827b34f260849208c95f28","source_sha256":"df83ca9db03a72c22da12838254915c3b34a9a4ac7f057340c454b73bc0055b4","composite_pages":[23,24,25,26,27,28],"initials_reviewed":10,"signatures_reviewed":3,"dates_reviewed":3,"current_geometry_matches":true,"visual_review":"passed","all_form_cases_passed":false,"evidence":"docs/release-evidence/txr1506-recovered-ordinary-provider-qa-2026-10-14.md"}}'::jsonb,
    updated_at = now()
where id = 'c136e9af-3340-403c-b178-c97fc4c74921'
  and slug = 'txr-1506-general-information-notice'
  and status = 'in_progress'
  and qa_status = 'partial'
  and current_release = '6ba8ae7c / dpl_C7SiC4BRwcsuAZjjEcLbE87LB4Ro (2026-09-22)'
  and metadata ->> 'revision' = '06-15-26'
returning id, slug, status, qa_status, current_release, known_issues, next_action;

-- Independently read back this exact UUID. Do not remove scope/version guards
-- or change status/qa_status to passed if the expected record no longer matches.
