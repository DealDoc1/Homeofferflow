-- Add the native mobile-app initiative to the authoritative product roadmap.
-- The current responsive web app remains the supported mobile experience until
-- the companion-app scope, security model, and release QA are complete.

insert into public.hof_roadmap_items (
  slug,
  category,
  title,
  description,
  priority,
  status,
  environment,
  qa_status,
  target_release,
  current_release,
  known_issues,
  next_action,
  requested_by,
  is_locked,
  metadata
) values (
  'mobile-app',
  'Platform',
  'HomeOfferFlow mobile app',
  'Build a secure cross-platform iOS and Android companion app for authenticated HomeOfferFlow users, beginning with agent workflows, offer status, notifications, and mobile document preparation.',
  30,
  'deferred',
  'backlog',
  'not_tested',
  'Post-web-workflow stabilization',
  null,
  'No native app exists yet. The responsive web app remains the supported mobile experience until the mobile authentication, secure data access, push-notification, offline-data, app-store, and release-QA plans are approved.',
  'Define the mobile-app product brief and architecture after web agent workflows, brokerage access controls, and subscription lifecycle monitoring are stable. Reuse the existing Supabase authorization model; do not ship an app that broadens buyer or offer-data access.',
  'Andrew Christian',
  false,
  '{"platforms":["iOS","Android"],"scope":"agent-first companion app","requires":["mobile authentication review","RLS verification","push-notification design","app-store release plan","mobile QA"]}'::jsonb
)
on conflict (slug) do update set
  category = excluded.category,
  title = excluded.title,
  description = excluded.description,
  priority = excluded.priority,
  status = excluded.status,
  environment = excluded.environment,
  qa_status = excluded.qa_status,
  target_release = excluded.target_release,
  known_issues = excluded.known_issues,
  next_action = excluded.next_action,
  requested_by = excluded.requested_by,
  is_locked = excluded.is_locked,
  metadata = excluded.metadata;

-- Verification after applying:
-- select slug, title, status, environment, metadata
-- from public.hof_roadmap_items where slug = 'mobile-app';
