-- Distinguish an explicitly granted no-charge beta partner from a paid lead.
-- Existing applications remain commercial by default; this does not mark them paid.
alter table public.hof_partner_leads
  add column if not exists partner_program text not null default 'commercial'
    check (partner_program in ('commercial', 'beta'));

comment on column public.hof_partner_leads.partner_program is
  'Commercial or explicitly granted no-charge beta program. Beta status never implies payment or automatic paid conversion.';
