begin;
set local lock_timeout = '5s';

-- Optional explicitly public creative on the existing central application.
-- No backfill from private contacts/photos and no grants, RLS or activation change.
alter table public.hof_partner_leads
  add column if not exists onboarding_public_headshot_url text;
alter table public.hof_partner_leads
  add constraint hof_partner_public_headshot_format check (
    onboarding_public_headshot_url is null or (
      char_length(onboarding_public_headshot_url) <= 500
      and onboarding_public_headshot_url ~ '^https://[^[:space:]<>]+$'
    )
  );
comment on column public.hof_partner_leads.onboarding_public_headshot_url is
  'Partner-approved public headshot only, displayed for active platform placements. Never populated from private account photos.';
notify pgrst,'reload schema';
commit;
