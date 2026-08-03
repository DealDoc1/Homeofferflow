-- Record the read-only production policy/launch-surface audit without
-- changing customer access, subscriptions, packet generation, or form gates.

begin;

update public.hof_roadmap_items
set current_release = 'd9eb70b production runtime + live policy audit 2026-08-03',
    updated_at = now()
where slug = 'production-deployment-checklist';

update public.hof_roadmap_items
set current_release = 'dec44ba live policy audit evidence reconciled 2026-08-03',
    updated_at = now()
where slug = 'supabase-product-tracker';

commit;

-- Verification:
-- select slug, current_release, updated_at
-- from public.hof_roadmap_items
-- where slug in ('production-deployment-checklist', 'supabase-product-tracker');
