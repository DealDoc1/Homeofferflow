-- Premier inventory is sold as one active category-and-market placement.
-- Normalize whitespace/case so harmless presentation differences cannot
-- create duplicate exclusivity claims. This applies only to active Premier
-- placements; Core and Featured inventory remains non-exclusive.

create unique index if not exists hof_partner_placements_active_exclusive_market_key
  on public.hof_partner_placements (
    partner_type,
    lower(btrim(market_area))
  )
  where is_active is true
    and placement_tier = 'exclusive_market'
    and partner_type is not null
    and market_area is not null;

comment on index public.hof_partner_placements_active_exclusive_market_key is
  'Prevents more than one active Premier Partner placement in the same category and normalized market area.';
