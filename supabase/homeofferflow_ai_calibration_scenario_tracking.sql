-- Track which documented anonymized calibration case a professional reviewed.
-- API validation enforces the five-value allowlist; legacy notes remain
-- readable but cannot satisfy the complete-scenario release gate.

begin;

alter table public.hof_feedback
  add column if not exists calibration_scenario text;

create index if not exists hof_feedback_ai_calibration_scenario_idx
  on public.hof_feedback (calibration_scenario, created_at desc)
  where issue_type = 'ai_review';

commit;

-- Verification:
-- select calibration_scenario, count(*)
-- from public.hof_feedback
-- where issue_type = 'ai_review'
-- group by calibration_scenario;
