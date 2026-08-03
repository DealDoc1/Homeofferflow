-- Record the verified active brokerage-admin account precondition without overclaiming
-- authenticated UI QA or packet/signature propagation.
-- This is generic product-state language: no named broker is a product gate.

update public.hof_roadmap_items
set
  current_release = '0f9e6a3 account profile retry-state hardening (production 2026-08-03)',
  known_issues = 'Account profile failures now surface a privacy-safe retry state instead of an indefinite brokerage loading state. Automated coverage includes invite creation, email binding, acceptance, membership connection, seat caps, and expiry closure. Authenticated browser QA for branding, shared defaults, roster visibility, invitations, and packet/signing propagation remains outstanding.',
  next_action = 'Run the generic brokerage-admin live QA checklist with an authenticated administrator, then verify one invitation and packet/signing-message propagation before marking the workspace passed.',
  updated_at = now()
where slug in ('admin-dashboard', 'broker-dashboard', 'brokerage-branding', 'team-support');

-- Verification:
-- select slug, status, environment, qa_status, current_release, next_action
-- from public.hof_roadmap_items
-- where slug in ('admin-dashboard', 'broker-dashboard', 'brokerage-branding', 'team-support')
-- order by slug;
