-- Keep the operational roadmap generic: any brokerage administrator can
-- exercise a brokerage workspace after they create an account and accept an
-- active membership. No named broker is a product gate or platform authority.

update public.hof_roadmap_items
set
  known_issues = 'Brokerage workspace features are live, but require a real signed-in brokerage administrator and at least one active brokerage membership for end-to-end smoke testing. Support access requires its own authenticated account if it will be used.',
  next_action = 'Run live brokerage-admin QA for branding, shared defaults, roster visibility, and one real agent invitation. Implement brokerage-controlled role delegation only after a concrete access policy is approved.'
where slug in ('admin-dashboard', 'broker-dashboard', 'brokerage-branding', 'team-support');

-- Verification after applying:
-- select slug, next_action from public.hof_roadmap_items
-- where slug in ('admin-dashboard', 'broker-dashboard', 'brokerage-branding', 'team-support');
