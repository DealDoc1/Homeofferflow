-- Tracker only: same reserved fictional document, verified and dispatched once
-- in the provider UI. No signing request, customer data or permissions change.
update public.hof_qa_runs
set notes = (notes::jsonb || jsonb_build_object(
  'phase', 'created', 'provider_status', 'sent', 'controls_verified', true,
  'dispatch_method', 'provider_ui_same_verified_draft',
  'dispatch_verified_at', now(),
  'dispatch_evidence', 'ordinary-listing-provider-2026-10-19/provider-sent.jpg',
  'delivery_evidence', 'owner QA invitation 1a15727c91f78612',
  'readback_checks', jsonb_build_object(
    'document_id', true, 'test_mode', true, 'name', true,
    'parallel_invitations', true, 'metadata', true,
    'geometry_and_recipients', true, 'completion_controls', true,
    'field_set', true, 'checkbox_groups', true, 'conditional_rules', true)
))::text
where id = 'c7ac1904-9e6a-41bd-b262-06912dc314af'
  and release_name = 'txr1101-ordinary-listing-lead-2026-10-19-v1'
  and environment = 'production'
  and notes::jsonb->>'phase' = 'draft_unverified'
  and notes::jsonb->>'document_id' = 'a2fa604d-6313-4ad8-97ea-290d029f28d0'
  and notes::jsonb->>'layout_sha256' = '49c620a7f1f61a21385b65085f53a218bc8b9f4f4214686b56a8a31c7cbe2533'
returning id, notes::jsonb->>'phase' as phase,
  notes::jsonb->>'document_id' as document_id;
