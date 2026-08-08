-- Record local unsigned signer-placement QA without enabling restricted forms.

update public.hof_roadmap_items
set current_release = 'local TXR signer-placement visual recheck (2026-08-08)',
    known_issues = 'Local unsigned renders and debug field-box overlays passed for TXR-1501, TXR-1506, TXR-1507, and TXR-1508. Authenticated preview and completed signed-PDF visual evidence are still required.',
    next_action = 'Run the authenticated one- and two-client preview matrix, download completed signed PDFs, and visually inspect every field, checkbox, initials, signature, and date before restricted production enablement.',
    updated_at = now()
where slug in (
  'txr-1501-long-buyer-tenant-representation',
  'txr-1506-general-information-notice',
  'txr-1507-short-buyer-tenant-representation',
  'txr-1508-unrepresented-showing'
);
