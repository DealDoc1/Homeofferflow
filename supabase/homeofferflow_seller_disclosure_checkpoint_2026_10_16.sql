-- Operational tracker correction only. No schema, workflow or permission change.
begin;
set local statement_timeout = '5s';
do $$
declare matched integer;
begin
  update public.hof_roadmap_items
  set known_issues = 'Agent-private seller leads and sale/lease listing workspaces remain live. Draft PR #1341 now implements disclosure explanation capture, lossless continuation pages, corrected source response anchors, Unknown preservation, conditional questions and revision-bound Seller review. These fixes are locally tested, not deployed. The candidate incorporates current production d8d2f1ae9fed3612594b4285690c65bb5132357c and reserves offline shell v105. Existing fictional v4 test b4ea4029-7e80-460c-880c-9e7275cee423 was last verified Sent with both signers prepared at final electronic-disclosure acceptance; corrected completed-provider PDF review remains unverified. The Mac is currently locked, and no usable SignWell credential is configured in the protected QA runner. Integrated authenticated Seller review/signing QA and the coordinated migration/API release remain incomplete. Source-specific sale/lease listing agreements also remain unimplemented; the shared source catalog has no TXR-1101 or TXR-1102 entry. No brokerage-seat, source-owner or per-agent approval requirement has been added.',
      next_action = 'Finish the existing v4 disclosure test after packet-specific electronic-disclosure consent or owner completion; do not recreate or resend it. Review its actual completed PDF and finish integrated authenticated Seller review/signing QA, then coordinate the pending review-version migration and API release. Implement source-specific sale/lease listing agreements from current source PDFs when available. Preserve parallel invitations, source access and pricing; local tests do not establish a completed-provider or full Seller-suite pass.',
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'seller_disclosure_local_checkpoint_2026_10_16', jsonb_build_object(
          'candidate_commit', '51f868e06e7fd097e9ade139240aae0c8456b64a',
          'pull_request', 1341,
          'production_baseline', 'd8d2f1ae9fed3612594b4285690c65bb5132357c',
          'candidate_deployed', false,
          'explanation_implementation', 'locally_tested',
          'completed_provider_review', 'not_verified',
          'integrated_authenticated_signing', 'not_verified',
          'provider_document_id', 'b4ea4029-7e80-460c-880c-9e7275cee423',
          'evidence', 'docs/release-evidence/seller-disclosure-continuation-2026-10-16.md')),
      updated_at = now()
  where id = '56d51351-422f-4d27-88f7-54cd8ba3734c'
    and slug = 'seller-workflow' and status = 'in_progress' and qa_status = 'partial'
    and current_release = 'PR #1330 / 83241c3 / listing-to-disclosure handoff and mobile field sizing (2026-10-13)'
    and md5(coalesce(metadata, '{}'::jsonb)::text) = '9ecfcf8b76c6859bbd0f595185ee3d0a'
    and md5(coalesce(known_issues, '')) = '457896fd85d927120f992ef0390ccde2'
    and md5(coalesce(next_action, '')) = '958ba6222fad7fa2a0ab6c57992151ec';
  get diagnostics matched = row_count;
  if matched <> 1 then raise exception 'Expected exact seller-workflow checkpoint baseline; nothing updated'; end if;
end $$;
commit;
