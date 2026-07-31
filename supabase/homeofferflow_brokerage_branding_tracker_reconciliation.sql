-- Reconcile the brokerage branding roadmap item with the implemented
-- broker-admin-only Storage upload and branding update flow.
-- This does not mark the broader branding release complete: packet/email
-- propagation and authenticated live brokerage-admin QA remain outstanding.

update public.hof_roadmap_items
set
  known_issues = 'Broker-admin-only logo upload and brand-color editing are implemented. Packet/email propagation and authenticated live brokerage-admin QA remain outstanding.',
  next_action = 'Run authenticated brokerage-admin QA for logo upload, color saving, shared defaults, roster visibility, and one invitation; then verify packet/email branding propagation before marking complete.',
  current_release = 'Broker-admin branding storage and update flow implemented; propagation QA pending (2026-07-31)',
  updated_at = now()
where slug = 'brokerage-branding';

-- Verification after applying:
-- select slug, status, environment, qa_status, current_release, known_issues,
--        next_action
-- from public.hof_roadmap_items
-- where slug = 'brokerage-branding';
