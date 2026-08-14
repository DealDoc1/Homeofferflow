-- Record the verified public FSBO campaign-copy correction without changing
-- seller intake, pricing, checkout, provider selection, or form scope.

update public.hof_roadmap_items
set
  current_release = 'a1980c0 production: FSBO campaign CTA package-label alignment (2026-08-14)',
  known_issues = 'Seller package requests remain no-checkout intake. Provider directory access is optional, neutral, and never a referral, endorsement, or required provider choice. Regulated services still require appropriate provider confirmation.',
  next_action = 'Use package-specific seller landing views, CTA selections, submitted requests, provider-directory opens, and outbound clicks before introducing any paid seller checkout or provider ranking changes.',
  updated_at = now()
where slug = 'fsbo-workflow';
