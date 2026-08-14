-- Paid partners can complete pre-activation creative details through a
-- single-use, expiry-bound link. This never activates a public placement.
alter table public.hof_partner_leads
  add column if not exists onboarding_token_hash text,
  add column if not exists onboarding_token_expires_at timestamptz,
  add column if not exists onboarding_completed_at timestamptz,
  add column if not exists onboarding_website_url text,
  add column if not exists onboarding_logo_url text,
  add column if not exists onboarding_cta_label text,
  add column if not exists onboarding_market_area text;

create index if not exists hof_partner_leads_onboarding_token_idx
  on public.hof_partner_leads(onboarding_token_hash)
  where onboarding_token_hash is not null;

comment on column public.hof_partner_leads.onboarding_token_hash is
  'SHA-256 hash of the single-use paid-partner onboarding token; raw tokens are never stored.';
comment on column public.hof_partner_leads.onboarding_completed_at is
  'Server-recorded creative setup completion; this does not authorize a public placement.';
