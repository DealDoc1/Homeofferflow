-- Operational QA evidence only: preserve source, access, release and partial states.
begin;
set local statement_timeout = '5s';
do $$
declare matched integer;
begin
  update public.hof_roadmap_items
  set known_issues = concat_ws(' ', nullif(known_issues, ''),
        'One controlled seven-page amendment matrix was created on October 14; all 24 field positions match the reviewed map. Completed-provider visual review remains outstanding.'),
      next_action = 'Finish the existing TREC-39-11 test 521119a1-e2d8-41eb-86c9-c200d0096622 in the two approved inboxes; first signer fields are prepared at the electronic-disclosure step. Do not resend. Then review the completed signatures and continuation initials.',
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'amendment_provider_qa_2026_10_14', jsonb_build_object(
          'qa_revision', 'trec-39-11-placement-2026-10-14-static-source-v2',
          'qa_run_id', '8d192fb8-76fd-4236-9040-d3f21f1bbf24',
          'provider_document_id', '521119a1-e2d8-41eb-86c9-c200d0096622',
          'source_sha256', 'd12909bcbd014080948eb6f9771231ba1b1d98c64eaf07e87ab0faa1118b8d36',
          'packet_sha256', '82af16e4f7542474c723eab9aa7dbb795bd76a38fdb8603b7a1bf80b6f4078f3',
          'fields_sha256', '8b7e2fc87889ab1816e534be095edb0897d3ffc130d762025e70781f525ca6ee',
          'pages', 7, 'fields', 24, 'cases', 5, 'test_mode', true,
          'first_signer_fields_prepared', 13, 'completed_pdf_visual_review', 'pending',
          'all_form_cases_passed', false,
          'controller_release', 'PR #1339 / 32ab11f / dpl_C9CAxDShcosKDjYov6LoqYpjpF64',
          'evidence', 'docs/release-evidence/amendment-controlled-provider-qa-2026-10-14.md')),
      updated_at = now()
  where id = 'a52da3d1-8f8e-48d0-9914-191e814c1934'
    and slug = 'additional-texas-forms'
    and status = 'in_progress' and qa_status = 'partial'
    and current_release = 'PR #1312 / ee90d4d / dpl_FwBNH37LDFErdd1HQ9StV5oWGUz7 (2026-10-11)'
    and next_action = 'Complete controlled nonbinding parallel Buyer/Seller SignWell QA using the two approved test inboxes and visually inspect completed signatures and continuation initials.'
    and md5(coalesce(metadata, '{}'::jsonb)::text) = '5dde48676de4c4f7f2779a2b517e2816';
  get diagnostics matched = row_count;
  if matched <> 1 then raise exception 'Expected exact amendment QA tracker baseline; nothing updated'; end if;
end $$;
commit;
