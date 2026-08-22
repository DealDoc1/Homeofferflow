-- Reconcile the authoritative roadmap with verified production availability.
-- These are private-draft releases only; this migration does not enable or
-- change any signature-send behavior.

begin;

update public.hof_roadmap_items
set
  status = 'in_progress',
  environment = 'production',
  qa_status = 'partial',
  current_release = 'b0eb771 shared TXR library agent access and workspace copy reconciliation (2026-08-22)',
  known_issues = case slug
    when 'txr-1501-long-buyer-tenant-representation' then 'Approved TXR-1501 sources and signed-in-agent private drafting are live. Completed signature PDF visual QA is still required before describing a general signature release.'
    when 'txr-1506-general-information-notice' then 'Approved TXR-1506 sources and signed-in-agent private drafting are live. Completed acknowledgement-signature PDF visual QA is still required before describing a general signature release.'
    when 'mineral-reservation-addendum' then 'The TXR-1905 guided private-review draft and exact approved source are live. It intentionally has no signature-send route in this release.'
  end,
  next_action = case slug
    when 'txr-1501-long-buyer-tenant-representation' then 'Complete authenticated one- and two-client preview QA, then complete the signer matrix and completed-signature visual inspection before public signature-release language.'
    when 'txr-1506-general-information-notice' then 'Complete authenticated consumer-notice preview QA, then complete the signer matrix and completed-signature visual inspection before public signature-release language.'
    when 'mineral-reservation-addendum' then 'Use the new private-review workflow, measure demand, and add a dedicated signature route only after a source-specific signer map and completed-signature visual QA.'
  end
where slug in (
  'txr-1501-long-buyer-tenant-representation',
  'txr-1506-general-information-notice',
  'mineral-reservation-addendum'
);

commit;
