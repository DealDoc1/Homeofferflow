-- Record the verified production TXR-1914 private-review workflow. This
-- migration does not add a loan-document, signing, or send capability.

begin;

update public.hof_roadmap_items
set
  status = 'in_progress',
  environment = 'production',
  qa_status = 'partial',
  current_release = 'd595b19 guided TXR-1914 seller-financing private review draft (2026-08-22)',
  known_issues = 'The TXR-1914 guided private-review draft and exact approved source are live. It intentionally has no loan-document, signature-send, or completed-signature route in this release.',
  next_action = 'Measure use of the guided private-review workflow and add a signature route only after a source-specific signer map and completed-signature visual QA.'
where slug = 'seller-financing';

commit;
