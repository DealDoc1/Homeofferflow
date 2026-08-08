begin;

update public.hof_roadmap_items
set
  current_release = 'AI calibration reviewer-role threshold hardening (staged 2026-07-31)',
  known_issues = 'The staged dashboard counts only anonymized AI-review notes from agents, brokers, or brokerage administrators toward the five-scenario threshold. It has not been bundled into the next intentional Vercel production release. Human calibration review is still required.',
  next_action = 'Bundle the staged safeguard into the next intentional production deployment, then collect and document five anonymized broker/agent calibration scenarios before changing scoring or wording.',
  updated_at = now()
where slug = 'ai-offer-competitiveness';

commit;

