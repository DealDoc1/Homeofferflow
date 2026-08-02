-- Reconcile the product tracker after the anonymized AI calibration fixture
-- pack is merged. This does not approve a model/scoring change.

update public.hof_roadmap_items
set
  status = 'in_progress',
  environment = 'production',
  qa_status = 'partial',
  current_release = '9c9e773 AI calibration fixture pack',
  known_issues = 'Five anonymized calibration inputs are documented and machine-validated; no expert review records are complete yet.',
  next_action = 'Run AI-CAL-01 through AI-CAL-05 through the deployed review interface and record independent Texas broker or agent review before changing scoring or wording.',
  updated_at = now()
where slug = 'ai-offer-competitiveness';

-- Verification:
-- select slug, status, qa_status, current_release, known_issues, next_action
-- from public.hof_roadmap_items
-- where slug = 'ai-offer-competitiveness';
