-- Reconcile buyer-relationship roadmap items with the private draft
-- foundations already present in the product. These records are intentionally
-- source-gated: a draft foundation is not an executable, sendable, or signable
-- Texas REALTORS form.

begin;

update public.hof_roadmap_items
set
  status = 'blocked',
  environment = 'source_gate',
  qa_status = 'partial',
  current_release = '259c6ee TXR-1507 unsigned one/two-client render recheck (2026-08-08)',
  known_issues = 'Approved private source records and brokerage authorization are live for the supplied TXR sources. Local unsigned previews pass source/render checks, but authenticated point-of-use QA and controlled completed-signature visual QA remain open. Draft foundations cannot send or promote forms by themselves.',
  next_action = case slug
    when 'txr-1507-short-buyer-tenant-representation' then 'Run authenticated agent preview QA for one and two clients, then complete controlled signer-plan and completed-signature visual QA before production enablement.'
    when 'txr-1501-long-buyer-tenant-representation' then 'Run authenticated one- and two-client preview QA for the separate long form, then complete signer-plan and completed-signature visual QA; never substitute it for TXR-1507.'
    when 'txr-1508-unrepresented-showing' then 'Run authenticated preview QA for the separate no-representation workflow, then complete signer-plan and completed-signature visual QA before production enablement.'
    when 'txr-1506-general-information-notice' then 'Run authenticated preview QA for the separate consumer-notice acknowledgment, then complete signer-plan and completed-signature visual QA before production enablement.'
  end
where slug in (
  'txr-1507-short-buyer-tenant-representation',
  'txr-1501-long-buyer-tenant-representation',
  'txr-1508-unrepresented-showing',
  'txr-1506-general-information-notice'
);

commit;
