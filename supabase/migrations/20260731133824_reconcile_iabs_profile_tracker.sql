-- Reconcile the roadmap with the production agent-owned IABS feature.
insert into public.hof_roadmap_items
  (slug, category, title, description, priority, status, environment,
   qa_status, target_release, current_release, known_issues, next_action,
   github_ref, is_locked, metadata)
values
  (
    'agent-iabs-profile',
    'Agent Workspace',
    'Agent IABS profile attachment',
    'Private agent-owned IABS PDF storage with an explicit per-offer include choice.',
    19,
    'production',
    'production',
    'passed',
    null,
    'Production agent IABS profile attachment (2026-07-31)',
    null,
    'Monitor upload and optional-append errors; never attach an IABS automatically.',
    null,
    true,
    jsonb_build_object(
      'storage_bucket', 'agent-documents',
      'document_type', 'iabs',
      'automatic_attachment', false,
      'buyer_signature_fields', false
    )
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
  current_release = excluded.current_release,
  known_issues = excluded.known_issues,
  next_action = excluded.next_action,
  github_ref = excluded.github_ref,
  is_locked = excluded.is_locked,
  metadata = excluded.metadata,
  completed_at = coalesce(public.hof_roadmap_items.completed_at, now());

