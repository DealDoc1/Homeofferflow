-- Operational evidence only: preserve release, QA status and historical records.
begin;
set local statement_timeout = '5s';
do $$
declare matched integer;
begin
  update public.hof_roadmap_items
  set known_issues = 'Production seller/listing workspaces remain live. The candidate integrates production 61e516d0 and reserves shell v107; canonical production still serves v106. Seller-owned questionnaire, private answer saves, version-bound confirmations and combined TXR-1101 disclosure/water packet inclusion are implemented and locally tested, not deployed. Focused affected run: 230 tests passed; isolated PostgreSQL: 67 assertions passed. Actual-source 14/16/17-page cases and desktop/390px mobile UI were reviewed. Supplied and current official TREC disclosure sources render identically; source retrieval or source-owner authorization is not a blocker. Sale listing TXR-1101 is implemented locally; TXR-1102 remains unfinished. The existing v4 fictional disclosure test has one verified completed signer. The owner reports completing the second; latest provider readback still showed pending and no completed-provider proof is available. Do not recreate or resend the packet. Corrected v2 listing-lead provider QA, integrated authenticated disclosure signing, source registration and coordinated code/schema release remain unfinished. Purchase-offer combined disclosure inclusion remains separate. No brokerage-seat, source-owner or per-agent approval requirement has been added.',
      next_action = 'Obtain the existing second-signer v4 invitation or verified completed PDF and finish actual completed-provider placement review; packet-specific test consent is already authorized. Finish v2 listing-lead provider QA, then freeze one integrated candidate, run full regression once, coordinate pending schema/source/code activation and verify canonical production after one intentional release. Continue purchase-offer packet integration separately; incomplete disclosures must not stop other prepared documents. Do not recreate or resend the existing disclosure test.',
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'seller_disclosure_local_checkpoint_2026_10_19', jsonb_build_object(
          'candidate_commit', '954f0824', 'candidate_deployed', false,
          'production_baseline', '61e516d0a091646bbff14a00624051d4e328d4fc',
          'questionnaire', 'locally_tested', 'listing_combined_packet', 'locally_tested',
          'purchase_combined_packet', 'not_implemented',
          'affected_tests_passed', 230, 'isolated_postgres_assertions_passed', 67,
          'source_render_equivalence', 'verified_108dpi_all_pages',
          'provider_document_id', 'b4ea4029-7e80-460c-880c-9e7275cee423',
          'qa_a_status', 'completed_verified',
          'qa_b_status', 'owner_reports_complete_provider_proof_pending',
          'completed_provider_review', 'not_verified',
          'evidence', 'docs/release-evidence/listing-disclosure-packet-2026-10-18.md')),
      updated_at = now()
  where id = '56d51351-422f-4d27-88f7-54cd8ba3734c'
    and slug = 'seller-workflow' and status = 'in_progress' and qa_status = 'partial'
    and current_release = 'PR #1330 / 83241c3 / listing-to-disclosure handoff and mobile field sizing (2026-10-13)'
    and md5(coalesce(metadata, '{}'::jsonb)::text) = 'a3add73d20873988761c8e0018827f4a'
    and md5(coalesce(known_issues, '')) = 'd3b1ea957548696fbc3b87883e56c2b2'
    and md5(coalesce(next_action, '')) = '708499708884be666e6434c5d423ee06';
  get diagnostics matched = row_count;
  if matched <> 1 then raise exception 'Expected exact seller-workflow checkpoint baseline; nothing updated'; end if;
end $$;
commit;
