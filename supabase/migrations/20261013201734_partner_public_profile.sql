-- Nullable, explicitly public creative. Never copy internal contacts/messages.
-- Existing RLS and privileges remain unchanged. No automatic activation/billing.
alter table public.hof_partner_leads
  add column if not exists onboarding_public_contact_name text,
  add column if not exists onboarding_public_contact_phone text,
  add column if not exists onboarding_public_description text;

alter table public.hof_partner_leads
  add constraint hof_partner_public_name_length check (char_length(onboarding_public_contact_name) <= 80),
  add constraint hof_partner_public_phone_format check (onboarding_public_contact_phone ~ '^\+[1-9][0-9]{9,14}$'),
  add constraint hof_partner_public_description_length check (char_length(onboarding_public_description) <= 600);

comment on column public.hof_partner_leads.onboarding_public_contact_phone is
  'Explicitly approved public business number, displayed only for an active platform placement. Internal contact_phone never supplies this field.';
comment on column public.hof_partner_leads.onboarding_public_description is
  'Partner-approved public company description. Internal application messages remain private.';
