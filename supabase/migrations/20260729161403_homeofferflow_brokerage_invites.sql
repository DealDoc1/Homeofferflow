-- HomeOfferFlow brokerage agent invitations
-- This hardens the existing private, service-role-only invite table for the
-- broker-created OnDemand invite workflow. Browser clients retain no direct
-- read or write access to this table.

begin;

-- The table was created before this workflow and is currently empty. These
-- constraints make the server-side invite lifecycle explicit and auditable.
alter table public.hof_brokerage_invites
  alter column brokerage_id set not null,
  alter column role set not null,
  alter column status set not null,
  alter column invite_token set not null,
  alter column expires_at set not null;

alter table public.hof_brokerage_invites
  drop constraint if exists hof_brokerage_invites_role_check;

alter table public.hof_brokerage_invites
  add constraint hof_brokerage_invites_role_check
  check (role = 'agent');

alter table public.hof_brokerage_invites
  drop constraint if exists hof_brokerage_invites_status_check;

alter table public.hof_brokerage_invites
  add constraint hof_brokerage_invites_status_check
  check (status in ('pending', 'accepted', 'expired', 'revoked'));

create unique index if not exists hof_brokerage_invites_token_unique_idx
  on public.hof_brokerage_invites (invite_token);

-- A broker has one live invite per email. Expired/revoked history remains for
-- audit purposes while a replacement invite can be created safely.
create unique index if not exists hof_brokerage_invites_one_pending_email_idx
  on public.hof_brokerage_invites (brokerage_id, lower(email))
  where status = 'pending';

create index if not exists hof_brokerage_invites_pending_brokerage_idx
  on public.hof_brokerage_invites (brokerage_id, created_at desc)
  where status = 'pending';

-- Keep these invitation records private. The API verifies the broker or the
-- signed-in, email-matched invitee before using the service role to act.
alter table public.hof_brokerage_invites enable row level security;
revoke all on table public.hof_brokerage_invites from anon, authenticated;
grant all on table public.hof_brokerage_invites to service_role;

commit;


