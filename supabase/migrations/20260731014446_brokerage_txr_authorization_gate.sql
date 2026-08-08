-- Record a brokerage administrator's TXR/NAR authorization policy without
-- inferring membership from a license number or silently enabling forms.

begin;

alter table public.hof_brokerages
  add column if not exists txr_all_agents_authorized boolean not null default false,
  add column if not exists txr_authorization_attested_by uuid references auth.users(id) on delete set null,
  add column if not exists txr_authorization_attested_at timestamptz;

alter table public.hof_brokerages
  drop constraint if exists hof_brokerages_txr_authorization_attestation_check;

alter table public.hof_brokerages
  add constraint hof_brokerages_txr_authorization_attestation_check
  check (
    (txr_all_agents_authorized = false and txr_authorization_attested_by is null and txr_authorization_attested_at is null)
    or (txr_all_agents_authorized = true and txr_authorization_attested_by is not null and txr_authorization_attested_at is not null)
    or (txr_all_agents_authorized = false and txr_authorization_attested_by is not null and txr_authorization_attested_at is not null)
  );

comment on column public.hof_brokerages.txr_all_agents_authorized is
  'Brokerage administrator attestation that all participating agents are currently authorized Texas REALTORS/NAR users; this is not inferred from a license number.';

commit;

