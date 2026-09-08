-- Record the production availability of the shared TXR-1507 and TXR-1508
-- private-review workflows. This reconciliation does not enable a signature
-- route, alter any form source, or change a document's review-only scope.

begin;

update public.hof_roadmap_items
set
  status = 'in_progress',
  environment = 'production',
  qa_status = 'partial',
  current_release = 'guided shared TXR-1507 and TXR-1508 private-review drafts (2026-09-07)',
  known_issues = case slug
    when 'txr-1507-short-buyer-tenant-representation' then 'The guided TXR-1507 private review draft and shared approved source are available to every signed-in agent. It intentionally has no signature-send or completed-signature route in this release.'
    when 'txr-1508-unrepresented-showing' then 'The guided TXR-1508 unrepresented-customer private review draft and shared approved source are available to every signed-in agent. It intentionally has no signature-send or completed-signature route in this release.'
  end,
  next_action = case slug
    when 'txr-1507-short-buyer-tenant-representation' then 'Measure use of the private-review workflow and add a signature route only after a source-specific signer map and completed-signature visual QA.'
    when 'txr-1508-unrepresented-showing' then 'Measure use of the private-review workflow and add a signature route only after a source-specific signer map and completed-signature visual QA.'
  end
where slug in (
  'txr-1507-short-buyer-tenant-representation',
  'txr-1508-unrepresented-showing'
);

commit;
