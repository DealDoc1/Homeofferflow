begin;
update public.hof_roadmap_items
set
  environment = 'production',
  qa_status = 'partial',
  current_release = 'AI calibration reviewer-role threshold hardening (production 2026-07-31)',
  known_issues = 'Production now counts only anonymized AI-review notes from agents, brokers, or brokerage administrators toward the five-scenario threshold. Scoring and wording remain unchanged until human calibration review is complete.',
  next_action = 'Collect and document five anonymized broker/agent calibration scenarios, then review scoring and wording with human release authority before changing either.',
  updated_at = now()
where slug = 'ai-offer-competitiveness';
update public.hof_roadmap_items
set
  known_issues = 'Brokerage workspace features are live, but require a real signed-in brokerage administrator and at least one active brokerage membership for end-to-end smoke testing. Support access requires its own authenticated account if it will be used.',
  next_action = 'Run live brokerage-admin QA for branding, shared defaults, roster visibility, and one real agent invitation. Implement brokerage-controlled role delegation only after a concrete access policy is approved.',
  updated_at = now()
where slug in ('admin-dashboard','broker-dashboard','brokerage-branding','team-support');
commit;

