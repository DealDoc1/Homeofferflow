-- Reconcile buyer-relationship roadmap items with the private draft
-- foundations already present in the product. These records are intentionally
-- source-gated: a draft foundation is not an executable, sendable, or signable
-- Texas REALTORS form.

begin;

update public.hof_roadmap_items
set
  status = 'blocked',
  environment = 'source_gate',
  qa_status = 'not_tested',
  current_release = 'Private draft foundation',
  known_issues = 'OnDemand has no approved private source record. The draft foundation cannot expose, generate, send, or sign this Texas REALTORS form until a brokerage administrator uploads and attests to the current authorized source.',
  next_action = case slug
    when 'txr-1507-short-buyer-tenant-representation' then 'Tyler Demando must upload and approve the authorized TXR-1507 source. Then complete mapping, signer plan, rendered-PDF QA, and broker approval.'
    when 'txr-1501-long-buyer-tenant-representation' then 'Tyler Demando must upload and approve the authorized TXR-1501 source. Then complete its separate mapping, signer plan, rendered-PDF QA, and broker approval; never substitute it for TXR-1507.'
    when 'txr-1508-unrepresented-showing' then 'Tyler Demando must upload and approve the authorized TXR-1508 source. Then complete the separate no-representation workflow, signer plan, and rendered-PDF QA.'
    when 'txr-1506-general-information-notice' then 'Tyler Demando must upload and approve the authorized TXR-1506 source. Then complete the separate consumer-notice acknowledgment, signer plan, and rendered-PDF QA.'
  end
where slug in (
  'txr-1507-short-buyer-tenant-representation',
  'txr-1501-long-buyer-tenant-representation',
  'txr-1508-unrepresented-showing',
  'txr-1506-general-information-notice'
);

commit;
