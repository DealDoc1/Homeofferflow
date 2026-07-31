-- Reconcile the roadmap tracker with the verified production SEO and launch
-- scope release. This is tracker data only; it does not change checkout,
-- packet generation, legal-form access, or deployment configuration.

update public.hof_roadmap_items
set
  status = 'production',
  environment = 'production',
  qa_status = 'passed',
  current_release = '58784fa Production SEO hero and launch-scope copy (2026-07-31)',
  github_ref = '58784fa',
  known_issues = null,
  next_action = 'Monitor launch conversion and keep the Texas offer scope wording current as new agent forms are approved.',
  completed_at = coalesce(completed_at, now()),
  updated_at = now()
where slug = 'seo-hero-update';

-- Verification:
-- select slug, status, environment, qa_status, current_release,
--        github_ref, known_issues, next_action, completed_at
-- from public.hof_roadmap_items
-- where slug = 'seo-hero-update';
