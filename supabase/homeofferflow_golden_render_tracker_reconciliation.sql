-- Record the 2026-07-29 approved-baseline render run. This is an automated
-- regression signal only; completed-signature visual QA remains mandatory for
-- any new or changed legal-form release.

update public.hof_roadmap_items
set
  status = 'production',
  environment = 'production',
  qa_status = 'automated_passed',
  current_release = '11-scenario golden rendered-PDF baseline verified (2026-07-29)',
  known_issues = 'Image-baseline matching catches unintended rendering changes but does not replace human review of every applicable blank, checkbox, initial, signature, and date on a completed signed packet.',
  next_action = 'Run scripts/check_golden_packet_rendering.py after every packet assembly, PDF, field-mapping, or signature-placement change. Complete rendered signed-PDF QA before approving a legal-form release.',
  updated_at = now()
where slug = 'automated-visual-regression';

-- Verification:
-- select slug, status, qa_status, current_release, next_action
-- from public.hof_roadmap_items
-- where slug = 'automated-visual-regression';
