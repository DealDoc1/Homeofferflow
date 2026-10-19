-- Operational roadmap update only. Execute after canonical v108 verification.
begin;
set local statement_timeout = '5s';
do $$
declare matched integer;
begin
  update public.hof_roadmap_items
  set current_release = 'PR #1348/#1349/#1350 / a162d1ea / seller-owned questionnaire, corrected disclosure and readable account controls (2026-10-19)',
      known_issues = 'Seller-owned disclosure questionnaire, version-bound answer saves/reviews, standalone signing path and PDF open/download access are deployed with coordinated service-only database functions. Both signers completed the existing v4 provider test; completed PDF placement review passed. Canonical owner entry, approved source availability, fictional draft save and normal four-page PDF were verified; SignWell and Resend read-only connections are ready. The separate live seller email-code-to-signature application roundtrip has not been newly exercised after this deployment. Sale-listing TXR-1101 and combined listing disclosure/water packaging remain implemented locally, not deployed; TXR-1102 is unfinished. Listing-lead v2 completed-provider rendering remains unverified. Purchase-offer combined disclosure inclusion is not implemented. Existing documents remain usable while disclosure work is pending. No source-owner, brokerage-seat or per-agent approval requirement has been added.',
      next_action = 'Use one ordinary fictional disclosure for the remaining live seller email-code/save/review/confirm/sign orchestration acceptance when required; do not recreate the completed v4 stress bundle. Finish listing-lead v2 provider review and the preserved TXR-1101 combined listing release separately, with its pending migrations coordinated to code. Implement purchase-offer disclosure inclusion separately. Do not hold unrelated prepared documents for missing disclosures.',
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'seller_disclosure_production_release_2026_10_19', jsonb_build_object(
          'production_commit', 'a162d1ea629b139e1e23689d6ed36e08ef959b70',
          'pull_requests', jsonb_build_array(1348,1349,1350),
          'initial_workflow', '39324133277', 'contrast_workflow', '39325880560',
          'shell', 'v108', 'questionnaire_deployed', true,
          'approved_source_loaded', true, 'owner_draft_save', 'production_verified',
          'normal_production_pdf_pages', 4,
          'provider_document_id', 'b4ea4029-7e80-460c-880c-9e7275cee423',
          'qa_a_status', 'completed_verified', 'qa_b_status', 'completed_verified',
          'completed_provider_review', 'passed_exact_v4_map',
          'provider_pdf_sha256', '3ba4969659936ce930501bfba2434f6870cab0ecd472b3cd8cbc2defedb45829',
          'live_application_signing_roundtrip', 'not_newly_exercised',
          'listing_combined_packet', 'locally_tested_not_deployed',
          'purchase_combined_packet', 'not_implemented',
          'source_owner_blocker', false, 'regression_tests', 2756, 'environment_skips', 3,
          'evidence', 'docs/release-evidence/seller-questionnaire-release-2026-10-19.md')),
      updated_at = now()
  where id = '56d51351-422f-4d27-88f7-54cd8ba3734c'
    and slug = 'seller-workflow' and status = 'in_progress' and qa_status = 'partial'
    and current_release = 'PR #1330 / 83241c3 / listing-to-disclosure handoff and mobile field sizing (2026-10-13)'
    and md5(coalesce(metadata, '{}'::jsonb)::text) = '3717c02c06d9f7ef1d7851da005edb3e'
    and md5(coalesce(known_issues, '')) = '5fcea9fb86da29d54109563db9a24b24'
    and md5(coalesce(next_action, '')) = '9745a4b1072f9e578dc94dd603e0aea0';
  get diagnostics matched = row_count;
  if matched <> 1 then raise exception 'Seller-workflow checkpoint changed; nothing updated'; end if;
end $$;
commit;
