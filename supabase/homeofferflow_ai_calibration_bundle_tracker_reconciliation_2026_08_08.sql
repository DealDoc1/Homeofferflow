-- Record the reviewer-bundle milestone without treating it as calibration
-- evidence or changing AI scoring/release state.

update public.hof_roadmap_items
set status = 'in_progress',
    environment = 'production',
    qa_status = 'partial',
    current_release = 'e381f59 AI calibration reviewer bundle (2026-08-08)',
    known_issues = 'Five independent anonymized broker/agent reviews have not yet been recorded. Generated baselines and the reviewer bundle are not calibration evidence.',
    next_action = 'Collect one completed anonymized review for each of AI-CAL-01 through AI-CAL-05 through the authenticated review path, then document dispositions before changing scoring or wording.',
    updated_at = now()
where slug = 'ai-offer-competitiveness';

-- Verification:
-- select slug, status, environment, qa_status, current_release,
--        known_issues, next_action
-- from public.hof_roadmap_items
-- where slug = 'ai-offer-competitiveness';
