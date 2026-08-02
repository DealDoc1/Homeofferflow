-- Persist the individual agent attestation required at point of use for
-- restricted Texas REALTORS® / NAR member-form workflows.
-- This records an attestation; it does not infer membership from a license.

begin;

alter table public.hof_brokerage_members
  add column if not exists txr_agent_authorized boolean not null default false,
  add column if not exists txr_agent_attested_by uuid references auth.users(id) on delete set null,
  add column if not exists txr_agent_attested_at timestamptz;

alter table public.hof_brokerage_members
  drop constraint if exists hof_brokerage_members_txr_agent_attestation_check;

alter table public.hof_brokerage_members
  add constraint hof_brokerage_members_txr_agent_attestation_check
  check (
    (txr_agent_authorized = false and txr_agent_attested_by is null and txr_agent_attested_at is null)
    or (txr_agent_authorized = true and txr_agent_attested_by is not null and txr_agent_attested_at is not null)
  );

comment on column public.hof_brokerage_members.txr_agent_authorized is
  'Agent point-of-use attestation that the member is currently authorized to use the brokerage-approved Texas REALTORS® / NAR source form; not inferred from a license number.';

-- Browser clients must not write membership authorization columns. The
-- server endpoint records the authenticated user and timestamp after the
-- required point-of-use checkbox is submitted.
revoke update on table public.hof_brokerage_members from anon, authenticated;

update public.hof_roadmap_items
set
  current_release = '4d787ba Persist individual Texas REALTORS authorization attestations',
  known_issues = 'Brokerage and individual agent attestations are server-audited. Restricted TXR workflows remain source-gated and draft-only until approved source and completed visual QA gates are complete.',
  next_action = 'Apply this migration, then run authenticated agent point-of-use QA for one restricted-form draft. Do not activate signing until source-owner approval, signer-plan review, rendered-PDF QA, completed-signature QA, and product release authority are recorded.',
  updated_at = now()
where slug in (
  'txr-1507-short-buyer-tenant-representation',
  'txr-1501-long-buyer-tenant-representation',
  'txr-1508-unrepresented-showing',
  'txr-1506-general-information-notice'
);

commit;
