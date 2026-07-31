-- Reconcile the roadmap tracker with the verified secure brokerage
-- Texas REALTORS® / NAR authorization gate and the still-source-gated
-- buyer-relationship foundations.

begin;

update public.hof_roadmap_items
set
  current_release = '9eb03b4 Secure brokerage Texas REALTORS authorization control',
  known_issues = 'Brokerage authorization control is live and server-enforced. End-to-end broker QA still requires a real active brokerage administrator; restricted TXR workflows remain source-gated.',
  next_action = 'Run authenticated brokerage-admin QA for authorization status, source upload, branding, shared defaults, roster visibility, and one invitation. Do not activate a TXR workflow until an approved source revision and completed signed visual QA exist.',
  updated_at = now()
where slug in ('team-support', 'brokerage-branding', 'broker-dashboard', 'admin-dashboard');

update public.hof_roadmap_items
set
  current_release = '9eb03b4 Explicit Texas REALTORS/NAR authorization gate',
  known_issues = 'Private draft foundation and renderer QA exist, but no authorized private source record is available for this brokerage. No form is exposed, generated, sent, or signed.',
  next_action = 'An authorized source owner must upload and attest to the exact current source. Then complete signer-plan, rendered-PDF, completed-signature visual QA, and HomeOfferFlow release-authority approval.',
  updated_at = now()
where slug in (
  'txr-1507-short-buyer-tenant-representation',
  'txr-1501-long-buyer-tenant-representation',
  'txr-1508-unrepresented-showing',
  'txr-1506-general-information-notice'
);

commit;

-- Verification:
-- select slug, status, environment, qa_status, current_release, next_action
-- from public.hof_roadmap_items
-- where slug in (
--   'team-support', 'brokerage-branding', 'broker-dashboard', 'admin-dashboard',
--   'txr-1507-short-buyer-tenant-representation',
--   'txr-1501-long-buyer-tenant-representation',
--   'txr-1508-unrepresented-showing',
--   'txr-1506-general-information-notice'
-- );
