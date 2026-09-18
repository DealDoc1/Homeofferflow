-- Run only against an isolated QA database. No customer or production data.
-- No persistent schema changes; all fixtures are rolled back.
BEGIN;
SET LOCAL statement_timeout = '5s';
DO $qa$
DECLARE
  item uuid := gen_random_uuid();
  owner_id uuid := gen_random_uuid();
  changed integer;
BEGIN
  INSERT INTO public.hof_standalone_agreements
    (id, brokerage_id, agent_user_id, form_source_id, form_code, source_revision, client_names, agreement_data, updated_at)
    VALUES (item, gen_random_uuid(), owner_id, gen_random_uuid(), 'TXR-1507',
      'rollback-only-delivery-qa', '["QA Fixture"]', '{}', '2026-09-15T10:00:00Z');
  UPDATE public.hof_standalone_agreements SET signwell_document_id='rollback-only-'||item,
      updated_at='2026-09-15T10:00:01Z',
      agreement_data='{"_hof_signature_delivery":{"version":1,"phase":"prepared"}}'
    WHERE id=item AND agent_user_id=owner_id AND status IN ('draft','failed')
      AND signwell_document_id IS NULL AND updated_at='2026-09-15T10:00:00Z';
  GET DIAGNOSTICS changed=ROW_COUNT;
  IF changed<>1 THEN RAISE EXCEPTION 'initial claim failed: %',changed; END IF;
  UPDATE public.hof_standalone_agreements SET status='sent'
    WHERE id=item AND agent_user_id=owner_id AND status IN ('draft','failed')
      AND signwell_document_id IS NULL AND updated_at='2026-09-15T10:00:00Z';
  GET DIAGNOSTICS changed=ROW_COUNT;
  IF changed<>0 THEN RAISE EXCEPTION 'stale initial claim accepted'; END IF;
  UPDATE public.hof_standalone_agreements SET status='sent'
    WHERE id=item AND agent_user_id=gen_random_uuid()
      AND signwell_document_id='rollback-only-'||item AND updated_at='2026-09-15T10:00:01Z';
  GET DIAGNOSTICS changed=ROW_COUNT;
  IF changed<>0 THEN RAISE EXCEPTION 'wrong owner accepted'; END IF;
  UPDATE public.hof_standalone_agreements SET updated_at='2026-09-15T10:00:02Z',
      agreement_data='{"_hof_signature_delivery":{"version":1,"phase":"sending"}}'
    WHERE id=item AND agent_user_id=owner_id AND status IN ('draft','failed')
      AND signwell_document_id='rollback-only-'||item AND updated_at='2026-09-15T10:00:01Z';
  GET DIAGNOSTICS changed=ROW_COUNT;
  IF changed<>1 THEN RAISE EXCEPTION 'resume claim failed'; END IF;
  UPDATE public.hof_standalone_agreements SET status='sent'
    WHERE id=item AND agent_user_id=owner_id AND status IN ('draft','failed')
      AND signwell_document_id='rollback-only-'||item AND updated_at='2026-09-15T10:00:01Z';
  GET DIAGNOSTICS changed=ROW_COUNT;
  IF changed<>0 THEN RAISE EXCEPTION 'stale resume claim accepted'; END IF;
  UPDATE public.hof_standalone_agreements SET status='signed', signed_at='2026-09-15T10:00:03Z' WHERE id=item;
  UPDATE public.hof_standalone_agreements SET status='sent'
    WHERE id=item AND agent_user_id=owner_id AND status IN ('draft','failed')
      AND signwell_document_id='rollback-only-'||item;
  GET DIAGNOSTICS changed=ROW_COUNT;
  IF changed<>0 THEN RAISE EXCEPTION 'terminal state regressed'; END IF;
END $qa$;
SELECT 'passed' AS result, 6 AS assertions, 'rollback-only; no external sends; no persistent schema changes' AS scope;
ROLLBACK;
