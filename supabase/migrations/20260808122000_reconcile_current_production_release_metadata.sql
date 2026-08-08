-- Keep the roadmap tracker aligned with the actual current production
-- deployment. Metadata only: this does not change packet mappings, form
-- sources, signer plans, billing behavior, or offer generation.

update public.hof_roadmap_items
set
  current_release = 'b51fda5 [deploy-production] Release verified HomeOfferFlow main',
  updated_at = now()
where priority in (10, 14, 15, 27, 28, 29);

-- Verification:
-- select slug, current_release, environment, qa_status, next_action
-- from public.hof_roadmap_items
-- where priority in (10, 14, 15, 27, 28, 29)
-- order by priority;
