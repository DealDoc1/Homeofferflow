-- Reconcile the production tracker after the guarded September 22 release.
--
-- This is a data-only tracker reconciliation. It grants no form access,
-- changes no signing geometry, and creates no provider document. Apply only
-- after commit 6ba8ae7c1465bda11c499a2eb262f8b3b4320b34 is Ready on the
-- canonical production domains and workflow 35707699574 has passed.

begin;

insert into public.hof_releases (
  release_key,
  title,
  environment,
  status,
  qa_status,
  git_branch,
  commit_sha,
  github_pr,
  vercel_deployment_url,
  summary,
  known_issues,
  next_action,
  approved_by,
  approved_at,
  deployed_at
) values (
  'prod-2026-09-22-agent-conversion-bundle',
  'Agent conversion, focused workspace, and post-reset form release',
  'production',
  'deployed',
  'passed',
  'main',
  '6ba8ae7c1465bda11c499a2eb262f8b3b4320b34',
  'PRs #1274, #1278, and #1279',
  'https://homeofferflow-6cozf1vg3-dealdoc1s-projects.vercel.app',
  'Released privacy-safe acquisition attribution, the simplified property-listing workspace, the focused agent dashboard, and the accumulated post-reset form corrections through one guarded prebuilt production deployment. The full 2,408-test suite, release preflight, schema readiness, Vercel spend gate, canonical response, PWA smoke test, and production API/packet runtime passed.',
  'TXR-1506, TXR-1508, TXR-1948, TXR-1953, TXR-1954, and hydrostatic completed-provider matrices remain deliberately partial until the specifically required fresh signed-PDF cases are visually inspected.',
  'Run only the remaining compact provider QA cases, monitor privacy-safe conversion funnels, and bundle the next verified customer-value enhancements into one intentional production release.',
  'Andrew Christian',
  '2026-09-22T08:57:55Z'::timestamptz,
  '2026-09-22T09:02:11Z'::timestamptz
)
on conflict (release_key) do update set
  title = excluded.title,
  environment = excluded.environment,
  status = excluded.status,
  qa_status = excluded.qa_status,
  git_branch = excluded.git_branch,
  commit_sha = excluded.commit_sha,
  github_pr = excluded.github_pr,
  vercel_deployment_url = excluded.vercel_deployment_url,
  summary = excluded.summary,
  known_issues = excluded.known_issues,
  next_action = excluded.next_action,
  approved_by = excluded.approved_by,
  approved_at = excluded.approved_at,
  deployed_at = excluded.deployed_at,
  updated_at = now();

update public.hof_roadmap_items
set
  status = 'production',
  environment = 'production',
  qa_status = 'passed',
  current_release = '6ba8ae7c / dpl_C7SiC4BRwcsuAZjjEcLbE87LB4Ro / workflow 35707699574 (2026-09-22)',
  known_issues = null,
  next_action = case slug
    when 'focused-customer-interviews-modal-accessibility' then 'Monitor privacy-safe completion and abandonment signals across the four agent transaction choices; keep each interview focused and restore the prior page state when a dialog closes.'
    when 'agent-dashboard' then 'Monitor Question 1 to workspace conversion and repeat-offer use; keep secondary forms and support collapsed until the agent asks for them.'
    when 'subscription-usage-management' then 'Monitor OnDemand email-start, secure-link, checkout-return, renewal, limit, and billing-recovery signals without sending test-mode events to production.'
    when 'production-deployment-checklist' then 'Use the same exact-commit, schema-readiness, spend-reserve, prebuilt-deploy, and canonical-runtime gate for the next intentional release.'
  end,
  completed_at = coalesce(completed_at, '2026-09-22T09:02:11Z'::timestamptz)
where slug in (
  'focused-customer-interviews-modal-accessibility',
  'agent-dashboard',
  'subscription-usage-management',
  'production-deployment-checklist'
);

update public.hof_roadmap_items
set
  status = 'production',
  environment = 'production',
  qa_status = 'passed',
  current_release = '6ba8ae7c / dpl_C7SiC4BRwcsuAZjjEcLbE87LB4Ro / compact provider QA 4ec37d4c (2026-09-22)',
  known_issues = null,
  next_action = 'Keep the approved source, server-owned signer plan, simultaneous invitations, answer bounds, and locked execution geometry in the focused and golden regression suites.',
  completed_at = coalesce(completed_at, '2026-09-22T09:02:11Z'::timestamptz)
where slug in (
  'txr-1501-long-buyer-tenant-representation',
  'txr-1507-short-buyer-tenant-representation',
  'seller-financing',
  'loan-assumption',
  'environmental-assessment-addendum',
  'mineral-reservation-addendum'
);

update public.hof_roadmap_items
set
  environment = 'production',
  current_release = '6ba8ae7c / dpl_C7SiC4BRwcsuAZjjEcLbE87LB4Ro (2026-09-22)',
  qa_status = 'partial',
  known_issues = case slug
    when 'txr-1506-general-information-notice' then 'The corrected workflow is production-live. Single-signer completed-provider QA passed; the remaining signer and conditional-field cases still require completed-PDF visual review.'
    when 'txr-1508-unrepresented-showing' then 'The corrected workflow is production-live. The historical pre-correction packet remains failure evidence; one fresh one-customer and one genuine two-customer completed PDF still require visual review.'
    when 'paragraph4-residential-lease' then 'The corrected TXR-1953 path is production-live. Fresh corrected completed PDFs are still required for the remaining signer and combined-packet matrix.'
    when 'paragraph4-fixture-lease' then 'The corrected TXR-1954 path is production-live. Fresh corrected completed PDFs are still required for the remaining signer and combined-packet matrix.'
    when 'hydrostatic-addendum' then 'The guided hydrostatic purchase path and packet assembly are production-live. A compact completed-provider signing matrix still requires visual review.'
  end,
  next_action = case slug
    when 'txr-1506-general-information-notice' then 'Complete only the still-missing signer and conditional-field cases, download the completed provider PDFs, and inspect every applicable mark, initial, signature, and date.'
    when 'txr-1508-unrepresented-showing' then 'Create one compact corrected one-customer and one genuine two-customer QA packet, then visually inspect the completed provider PDFs before marking passed.'
    when 'paragraph4-residential-lease' then 'Create the smallest fresh corrected TXR-1953 provider QA set that covers the remaining signer and combined-packet cases; preserve all historical packets.'
    when 'paragraph4-fixture-lease' then 'Create the smallest fresh corrected TXR-1954 provider QA set that covers the remaining signer and combined-packet cases; preserve all historical packets.'
    when 'hydrostatic-addendum' then 'Create one compact synthetic completed-provider matrix for the hydrostatic path and inspect its completed PDF before marking passed.'
  end
where slug in (
  'txr-1506-general-information-notice',
  'txr-1508-unrepresented-showing',
  'paragraph4-residential-lease',
  'paragraph4-fixture-lease',
  'hydrostatic-addendum'
);

update public.hof_roadmap_items
set
  status = 'in_progress',
  environment = 'production',
  qa_status = 'partial',
  current_release = '6ba8ae7c / dpl_C7SiC4BRwcsuAZjjEcLbE87LB4Ro (2026-09-22)',
  known_issues = 'The production PWA provides installable app-like access and aggregate install/return telemetry. A separate native iOS or Android app has not been justified or funded.',
  next_action = 'Monitor native-prompt availability, accepted installs, first installed-app returns, and repeat-workspace use before spending on a separate native application.'
where slug = 'mobile-app';

commit;

-- Verification after applying:
-- select release_key, status, qa_status, commit_sha, vercel_deployment_url
-- from public.hof_releases
-- where release_key = 'prod-2026-09-22-agent-conversion-bundle';
--
-- select slug, status, environment, qa_status, current_release, known_issues,
--        next_action, completed_at
-- from public.hof_roadmap_items
-- where slug in (
--   'focused-customer-interviews-modal-accessibility', 'agent-dashboard',
--   'subscription-usage-management', 'production-deployment-checklist',
--   'txr-1501-long-buyer-tenant-representation',
--   'txr-1506-general-information-notice',
--   'txr-1507-short-buyer-tenant-representation',
--   'txr-1508-unrepresented-showing', 'seller-financing', 'loan-assumption',
--   'paragraph4-residential-lease', 'paragraph4-fixture-lease',
--   'hydrostatic-addendum', 'environmental-assessment-addendum',
--   'mineral-reservation-addendum', 'mobile-app'
-- )
-- order by priority, title;
