-- Operational evidence only; run after canonical release verification.
begin;
set local statement_timeout = '5s';
do $$
declare matched integer;
begin
  update public.hof_roadmap_items
  set current_release = 'PR #1351 / 4bd1cce5 / completed seller disclosure reuse with automatic buyer acknowledgments (2026-10-19)',
      known_issues = 'Seller questionnaire and corrected disclosure/PDF access remain deployed. A completed seller-only disclosure can now be selected for the matching purchase property without download/re-upload; its PDF/audit pages are preserved and current buyer acknowledgments are added automatically. The owner-only preparation API makes no provider send or database write. Reused exact v4 geometry has completed-provider proof; new composition, page identity, owner/property/duplicate/limit boundaries and mobile picker have local runtime/visual coverage. A newly completed combined purchase packet was not exercised live. Unsigned disclosure execution within a purchase request remains unfinished. TXR-1101 combined listing packet remains implemented locally, not deployed; TXR-1102 remains unfinished, and listing-lead v2 provider review is unverified. Existing prepared documents are not held for pending disclosure work. No source-owner, brokerage-seat or per-agent approval requirement is added.',
      next_action = 'Finish unsigned disclosure execution and purchase-package integration, then the preserved TXR-1101 listing release with its coordinated migrations and listing-lead v2 provider review. Reuse the already-completed v4 placement proof; do not send another multi-case stress bundle. Continue targeted live application acceptance without touching real client packets or claiming the whole seller suite complete.',
      metadata = coalesce(metadata,'{}'::jsonb) || jsonb_build_object(
        'purchase_disclosure_reuse_2026_10_19', jsonb_build_object(
          'pull_request',1351,'production_commit','4bd1cce57f052a587d6017d8782204ef521dfa41',
          'workflow','39329453051','shell','v109','completed_pdf_reuse','deployed',
          'buyer_receipt_geometry','reuses_completed_v4_calibration',
          'source_page_pixels_preserved',true,'focused_tests',74,'regression_tests',2765,'environment_skips',3,
          'local_browser_real_handler','passed_fictional_dependencies',
          'new_live_combined_provider_completion','not_exercised',
          'unsigned_combined_execution','not_implemented',
          'evidence','docs/release-evidence/purchase-disclosure-reuse-2026-10-19.md')),
      updated_at=now()
  where id='56d51351-422f-4d27-88f7-54cd8ba3734c' and slug='seller-workflow'
    and status='in_progress' and qa_status='partial'
    and current_release='PR #1348/#1349/#1350 / a162d1ea / seller-owned questionnaire, corrected disclosure and readable account controls (2026-10-19)'
    and md5(coalesce(metadata,'{}'::jsonb)::text)='6c290997bd1be37cf4ade96e349b0c71'
    and md5(coalesce(known_issues,''))='11de30a750e9a313b93362fb284dcf3d'
    and md5(coalesce(next_action,''))='cc7efb91540e55e77e1e3d08fab5d87e';
  get diagnostics matched=row_count;
  if matched<>1 then raise exception 'Seller-workflow checkpoint changed; nothing updated'; end if;
end $$;
commit;
