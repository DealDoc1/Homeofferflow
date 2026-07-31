-- Keep the AI roadmap honest about the difference between generated review
-- outputs and anonymized human calibration notes.

update public.hof_roadmap_items
set
  current_release = 'AI review output-vs-calibration dashboard distinction (2026-07-31)',
  known_issues = 'The limited educational AI review remains gated for expansion. The admin dashboard now separates generated review-output volume from anonymized human calibration notes; generated outputs do not satisfy the five-scenario expert-review threshold.',
  next_action = 'Collect at least five anonymized scenarios through the worksheet or AI review feedback path, have an experienced Texas broker or agent assess them, and document misleading, unsafe, or missing output before any scoring or wording expansion.',
  updated_at = now()
where slug = 'ai-offer-competitiveness';

-- Verification:
-- select slug, status, qa_status, current_release, known_issues, next_action
-- from public.hof_roadmap_items
-- where slug = 'ai-offer-competitiveness';
