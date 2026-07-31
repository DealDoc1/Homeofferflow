-- Targeted indexes for the brokerage/TXR rollout.
-- These cover foreign keys used by broker-admin authorization, invitations,
-- memberships, and private form-source audit records. They do not alter RLS
-- or grant any additional access.

begin;

create index if not exists hof_brokerage_form_sources_authorized_by_user_id_idx
  on public.hof_brokerage_form_sources (authorized_by_user_id);

create index if not exists hof_brokerage_invites_accepted_by_idx
  on public.hof_brokerage_invites (accepted_by);

create index if not exists hof_brokerage_invites_invited_by_idx
  on public.hof_brokerage_invites (invited_by);

create index if not exists hof_brokerage_members_invited_by_idx
  on public.hof_brokerage_members (invited_by);

create index if not exists hof_brokerage_members_user_id_idx
  on public.hof_brokerage_members (user_id);

create index if not exists hof_brokerages_created_by_idx
  on public.hof_brokerages (created_by);

create index if not exists hof_brokerages_txr_authorization_attested_by_idx
  on public.hof_brokerages (txr_authorization_attested_by);

commit;
