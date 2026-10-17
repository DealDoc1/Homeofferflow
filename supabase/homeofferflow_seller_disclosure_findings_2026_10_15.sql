-- Operational notes only. Do not promote an unreviewed form or alter access.
begin;
set local statement_timeout = '5s';
do $$
declare matched integer;
begin
  update public.hof_roadmap_items
  set known_issues = concat_ws(' ', nullif(known_issues, ''),
        'October 15 correctness audit found seventeen property-feature N/U choices rendering as affirmative checks and older response anchors off their rules. PR #1341 corrects these locally with visual and regression evidence; it is not deployed. The current disclosure interview also lacks several explanatory-answer inputs and the renderer does not yet carry those narratives through. This is additional unfinished implementation, not only completed-signature QA.'),
      next_action = 'Complete source-specific disclosure explanation capture and lossless PDF output. Finish the controlled integrated seller-disclosure signing review and release the reviewed response correction from PR #1341 without duplicate invitations. Implement the missing sale/lease listing agreements. Preserve existing source access, seller review, parallel invitations and pricing; do not mark the seller suite complete from narrow rendering tests.',
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'seller_disclosure_correctness_2026_10_15', jsonb_build_object(
          'candidate_commit', 'f36852970fb5c746bd72998c55db828ef9480017',
          'pull_request', 1341, 'response_lines', 17,
          'candidate_deployed', false, 'explanation_coverage_complete', false,
          'completed_provider_review', 'pending',
          'execution_widget_sha256', '4b9bcc58cfecdfaacbdc8c6ef9a1e69727d6d7daa6f94cc25be84f44a4815610',
          'evidence', 'docs/release-evidence/seller-disclosure-response-correction-2026-10-15.md')),
      updated_at = now()
  where id = '56d51351-422f-4d27-88f7-54cd8ba3734c'
    and slug = 'seller-workflow' and status = 'in_progress' and qa_status = 'partial'
    and current_release = 'PR #1330 / 83241c3 / listing-to-disclosure handoff and mobile field sizing (2026-10-13)'
    and md5(coalesce(metadata, '{}'::jsonb)::text) = '4760c0a6cdc81e69ee80db0ec6847380'
    and md5(coalesce(known_issues, '')) = 'ff0416b1930cd2826a23724611ea868b'
    and md5(coalesce(next_action, '')) = '058b79732923c703038928762e52900d';
  get diagnostics matched = row_count;
  if matched <> 1 then raise exception 'Expected exact seller-workflow audit baseline; nothing updated'; end if;
end $$;
commit;
