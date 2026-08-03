-- Record the production AI calibration evidence safeguard without claiming
-- that human calibration reviews are complete.

begin;

update public.hof_roadmap_items
set
  current_release = 'd9eb70b structured AI calibration review evidence (production 2026-08-03; dpl_9ouocpBidjaTrC7feae4UHHFEJzs)',
  known_issues = 'The production feedback form now captures useful, misleading or unsafe, insufficient or missing, disclaimer clarity, overclaiming risk, and reviewer disposition for anonymized AI-review notes. Human calibration review is still required; no scoring or wording change is approved.',
  next_action = 'Collect and document five anonymized broker/experienced-agent calibration scenarios using AI-CAL-01 through AI-CAL-05 before changing scoring or wording.',
  updated_at = now()
where slug = 'ai-offer-competitiveness';

commit;

-- Verification:
-- select slug, status, environment, qa_status, current_release, known_issues,
--        next_action
-- from public.hof_roadmap_items
-- where slug = 'ai-offer-competitiveness';
