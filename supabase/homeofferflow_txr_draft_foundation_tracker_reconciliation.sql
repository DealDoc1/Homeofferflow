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
  current_release = 'Unsigned local source/render QA verified 2026-08-03',
  known_issues = 'The privately supplied source identity and unsigned draft render passed locally, but no authorized private source record is available in the vault. The draft foundation cannot expose, generate, send, or sign this Texas REALTORS form until an authorized source-owner administrator uploads and attests to the current authorized source.',
  next_action = case slug
    when 'txr-1507-short-buyer-tenant-representation' then 'An authorized source owner must upload and attest to the TXR-1507 source. Then complete mapping, signer plan, rendered-PDF QA, and HomeOfferFlow release-authority approval.'
    when 'txr-1501-long-buyer-tenant-representation' then 'An authorized source owner must upload and attest to the TXR-1501 source. Then complete its separate mapping, signer plan, rendered-PDF QA, and HomeOfferFlow release-authority approval; never substitute it for TXR-1507.'
    when 'txr-1508-unrepresented-showing' then 'An authorized source owner must upload and attest to the TXR-1508 source. Then complete the separate no-representation workflow, signer plan, rendered-PDF QA, and HomeOfferFlow release-authority approval.'
    when 'txr-1506-general-information-notice' then 'An authorized source owner must upload and attest to the TXR-1506 source. Then complete the separate consumer-notice acknowledgment, signer plan, rendered-PDF QA, and HomeOfferFlow release-authority approval.'
  end
where slug in (
  'txr-1507-short-buyer-tenant-representation',
  'txr-1501-long-buyer-tenant-representation',
  'txr-1508-unrepresented-showing',
  'txr-1506-general-information-notice'
);

commit;
