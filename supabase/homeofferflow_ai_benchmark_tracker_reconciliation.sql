-- Record the automated AI-review benchmark that shipped in PR #42 while
-- retaining the required broker/expert calibration gate before expansion.

update public.hof_roadmap_items
set
  current_release = 'AI offer-review benchmark and live-response safety hardening (2026-07-29)',
  known_issues = 'The AI review remains a limited educational feature. Deterministic fallback benchmark coverage now verifies market-leverage and risk behavior; live model output is bounded and always receives HomeOfferFlow''s immutable educational disclaimer. It does not validate property valuation or professional advice.',
  next_action = 'Have an experienced Texas broker or agent compare anonymized real transaction scenarios against the output, document misleading or insufficient results, then calibrate before expanding the feature.',
  updated_at = now()
where slug = 'ai-offer-competitiveness';

-- Verification:
-- select slug, status, qa_status, current_release, known_issues, next_action
-- from public.hof_roadmap_items
-- where slug = 'ai-offer-competitiveness';
