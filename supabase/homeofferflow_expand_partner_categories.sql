-- HomeOfferFlow PR #10 follow-up: keep the production partner-lead database
-- constraint synchronized with the categories accepted by /api/fsbo-lead.
--
-- This script is intentionally separate from the baseline table definition so
-- it can be reviewed and applied to an existing Supabase project. It is safe to
-- rerun: the constraint is replaced inside one transaction and validated before
-- the transaction commits.

begin;

alter table public.hof_partner_leads
  drop constraint if exists hof_partner_leads_partner_type_check;

alter table public.hof_partner_leads
  add constraint hof_partner_leads_partner_type_check
  check (partner_type in (
    'title',
    'lender',
    'inspection',
    'surveyor',
    'home_warranty',
    'insurance',
    'roofing',
    'hvac',
    'plumbing',
    'electrical',
    'foundation_structural',
    'general_contractor',
    'pest_termite',
    'septic_well',
    'restoration',
    'photography_video',
    'staging',
    'repairs_handyman',
    'cleaning',
    'moving_storage',
    'lawn_pool',
    'security_smart_home',
    'other'
  )) not valid;

alter table public.hof_partner_leads
  validate constraint hof_partner_leads_partner_type_check;

commit;

-- Verification query: the returned definition must contain every category
-- accepted by api/fsbo-lead.py, including roofing and security_smart_home.
select
  c.conname,
  c.convalidated,
  pg_get_constraintdef(c.oid) as definition
from pg_constraint c
join pg_class t on t.oid = c.conrelid
join pg_namespace n on n.oid = t.relnamespace
where n.nspname = 'public'
  and t.relname = 'hof_partner_leads'
  and c.conname = 'hof_partner_leads_partner_type_check';
