-- Reconcile the AI calibration safeguard after the intentional production release.
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
commit;

