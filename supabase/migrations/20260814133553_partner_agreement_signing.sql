-- Tracks the separate HomeOfferFlow commercial partner agreement. This does
-- not change payment, onboarding, public placement, or any Texas REALTORS form.
alter table public.hof_partner_leads
  add column if not exists partner_agreement_status text not null default 'not_started'
    check (partner_agreement_status in ('not_started', 'sent', 'signed', 'declined', 'expired', 'void')),
  add column if not exists partner_agreement_signwell_document_id text,
  add column if not exists partner_agreement_sent_at timestamptz,
  add column if not exists partner_agreement_signed_at timestamptz;

create unique index if not exists hof_partner_leads_partner_agreement_document_id_key
  on public.hof_partner_leads(partner_agreement_signwell_document_id)
  where partner_agreement_signwell_document_id is not null;

create index if not exists hof_partner_leads_partner_agreement_status_idx
  on public.hof_partner_leads(partner_agreement_status, created_at desc);

comment on column public.hof_partner_leads.partner_agreement_status is
  'Lifecycle of the separate HomeOfferFlow commercial partner agreement. A signed agreement is required before public partner placement.';
comment on column public.hof_partner_leads.partner_agreement_signwell_document_id is
  'SignWell document ID for the commercial partner agreement; signing URLs and raw provider payloads are not stored.';
