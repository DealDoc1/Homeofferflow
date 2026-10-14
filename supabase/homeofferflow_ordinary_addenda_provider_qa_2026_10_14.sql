-- Operational QA evidence only. No source, access, release or status changes.
-- Run after immutable completed-PDF/source audit and all three-page visual review.
do $$
declare touched integer;
begin
  with reviewed(id, slug, form_code, component_page, source_digest, known_note, next_note) as (
    values
      ('78a39a5a-83e0-436a-a00a-ea2d127a068c'::uuid, 'hydrostatic-addendum', 'TREC-48-1', 21,
       '3eb6e7ced0723ceaab6bef2645fcd7868ee3c2cd2734a6a5f03dbe049bd5df6a',
       'The guided hydrostatic purchase path and packet assembly are production-live. The recovered ordinary two-buyer/two-seller completed-provider component passes current-map comparison and visual review of all four signatures. This is not proof of the full purchase-package or remaining signer/risk-allocation matrix.',
       'Reuse the covered ordinary four-party placement case instead of resending it. Complete only missing one-signer, risk-allocation and actual combined-purchase provider cases; preserve all historical packets and current customer maps.'),
      ('cf8cb9d9-7f25-4e2c-bff4-1082711d7c13'::uuid, 'paragraph4-residential-lease', 'TXR-1953', 31,
       '00075ab42b6d7f234c5e70197f02fadb736b2ff3ee02a0dc1f5499535b045fc3',
       'The corrected TXR-1953 path is production-live. The recovered ordinary two-buyer/two-seller completed-provider component passes current-map comparison and visual review of all four signatures. Remaining signer, long/Unicode continuation and actual combined-purchase cases are still unverified.',
       'Reuse the covered ordinary four-party placement case instead of resending it. Complete only missing signer, long/Unicode continuation and actual combined-purchase provider cases; preserve all historical packets and current customer maps.'),
      ('0d1ffe90-afc6-48ee-9be3-a0d5935f1729'::uuid, 'paragraph4-fixture-lease', 'TXR-1954', 32,
       'e96fe7d35245aee60920ba264ef870542199fa201e49382a6eac27718fabdc28',
       'The corrected TXR-1954 path is production-live. The recovered ordinary two-buyer/two-seller completed-provider component passes current-map comparison and visual review of all four signatures. Remaining signer, long/Unicode continuation and actual combined-purchase cases are still unverified.',
       'Reuse the covered ordinary four-party placement case instead of resending it. Complete only missing signer, long/Unicode continuation and actual combined-purchase provider cases; preserve all historical packets and current customer maps.')
  )
  update public.hof_roadmap_items as item
  set known_issues = reviewed.known_note,
      next_action = reviewed.next_note,
      metadata = coalesce(item.metadata, '{}'::jsonb) || jsonb_build_object(
        'completed_provider_ordinary_addenda_2026_10_14', jsonb_build_object(
          'case', 'ordinary_two_buyers_two_sellers',
          'form_code', reviewed.form_code,
          'provider_document_id', '13f7fe33-3620-4b61-b66e-4c96b5792c1f',
          'completed_sha256', 'd5dd3d701b06cff87934235680dbee1d40e56fe99d827b34f260849208c95f28',
          'source_sha256', reviewed.source_digest,
          'composite_page', reviewed.component_page,
          'signatures_reviewed', 4,
          'current_geometry_matches', true,
          'visual_review', 'passed',
          'all_form_cases_passed', false,
          'combined_packet_assembly_verified', false,
          'evidence', 'docs/release-evidence/ordinary-addenda-completed-provider-qa-2026-10-14.md')),
      updated_at = now()
  from reviewed
  where item.id = reviewed.id
    and item.slug = reviewed.slug
    and item.status = 'in_progress'
    and item.qa_status = 'partial'
    and item.current_release = '6ba8ae7c / dpl_C7SiC4BRwcsuAZjjEcLbE87LB4Ro (2026-09-22)'
    and md5(coalesce(item.metadata, '{}'::jsonb)::text) = case item.id
      when '78a39a5a-83e0-436a-a00a-ea2d127a068c'::uuid then '199b2e7a6802f6a063d2b068a99ca4db'
      when 'cf8cb9d9-7f25-4e2c-bff4-1082711d7c13'::uuid then 'be2705cfcd1e9692c4e1e6616b015543'
      when '0d1ffe90-afc6-48ee-9be3-a0d5935f1729'::uuid then '33a64859590c41730cba8c13ab508838'
      end
    and not (coalesce(item.metadata, '{}'::jsonb) ? 'completed_provider_ordinary_addenda_2026_10_14');
  get diagnostics touched = row_count;
  if touched <> 3 then
    raise exception 'Expected exactly three unchanged partial QA rows; updated %', touched;
  end if;
end $$;

-- Read back separately by the exact three UUIDs and compare prior metadata after
-- removing only the new case key. Do not alter status or widen these targets.
