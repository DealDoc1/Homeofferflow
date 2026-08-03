-- Record the latest approved golden-packet rendering verification.

begin;

update public.hof_roadmap_items
set qa_status = 'automated_passed',
    current_release = '8fa16e0 all-supported-addenda golden render matches approved baseline (2026-08-03)',
    updated_at = now()
where slug = 'automated-visual-regression';

commit;

-- Verification:
-- select slug, qa_status, current_release, updated_at
-- from public.hof_roadmap_items
-- where slug = 'automated-visual-regression';
