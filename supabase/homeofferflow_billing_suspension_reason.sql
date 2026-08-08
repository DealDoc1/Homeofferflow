-- Distinguish a Stripe billing suspension from a broker's deliberate access
-- suspension. Without this field, a later successful renewal could silently
-- undo a broker decision, or a billing event could overwrite its reason.

begin;

alter table public.hof_brokerage_members
  add column if not exists suspension_reason text;

alter table public.hof_brokerage_members
  drop constraint if exists hof_brokerage_members_suspension_reason_check;

alter table public.hof_brokerage_members
  add constraint hof_brokerage_members_suspension_reason_check
  check (suspension_reason is null or suspension_reason in ('billing', 'manual'));

create index if not exists hof_brokerage_members_suspension_reason_idx
  on public.hof_brokerage_members (status, suspension_reason)
  where status = 'suspended';

commit;

-- Existing suspended memberships are intentionally left unchanged until an
-- administrator reviews them. New Stripe suspensions write 'billing'; the
-- broker dashboard writes 'manual'.
