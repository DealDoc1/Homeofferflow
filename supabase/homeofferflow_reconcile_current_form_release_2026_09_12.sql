-- Align the product tracker with the form capabilities staged on main.
--
-- This is deliberately a tracker reconciliation, not a schema migration.  It
-- must be run only after the accompanying application release is promoted;
-- nothing here grants access or changes a signing permission.
begin;

update public.hof_roadmap_items
set
  status = 'in_progress',
  environment = 'staging',
  qa_status = 'partial',
  current_release = 'guided shared-form review-and-send release staged on main (2026-09-12)',
  known_issues = case slug
    when 'txr-1507-short-buyer-tenant-representation' then 'The current staged build uses the calibrated TXR-1507 execution map and rejects older saved maps. A new completed provider-rendered packet is still required to confirm the released map visually.'
    when 'txr-1501-long-buyer-tenant-representation' then 'The current staged build has a dedicated review-and-send path. A new completed provider-rendered packet is still required to confirm the latest execution map visually.'
    when 'txr-1506-general-information-notice' then 'The current staged build has a dedicated review-and-send acknowledgement path. A new completed provider-rendered packet is still required to confirm the latest acknowledgement map visually.'
    when 'txr-1508-unrepresented-showing' then 'The current staged build has a dedicated review-and-send path. A new completed provider-rendered packet is still required to confirm the latest acknowledgement map visually.'
    when 'seller-financing' then 'The current staged build has a guided TXR-1914 review-and-send path. It does not create loan documents or provide financing advice.'
    when 'loan-assumption' then 'The current staged build has a guided TXR-1919 review-and-send path. It does not assess credit, contact a lender, or create loan documents.'
    when 'environmental-assessment-addendum' then 'The current staged build has a guided TXR-1917 review-and-send path. It does not perform an environmental assessment.'
    when 'mineral-reservation-addendum' then 'The current staged build has a guided TXR-1905 review-and-send path for source-form choices.'
  end,
  next_action = 'Promote the bundled release, send one controlled packet for each source-specific form map, and record completed provider-PDF visual verification.'
where slug in (
  'txr-1501-long-buyer-tenant-representation',
  'txr-1506-general-information-notice',
  'txr-1507-short-buyer-tenant-representation',
  'txr-1508-unrepresented-showing',
  'seller-financing',
  'loan-assumption',
  'environmental-assessment-addendum',
  'mineral-reservation-addendum'
);

commit;
