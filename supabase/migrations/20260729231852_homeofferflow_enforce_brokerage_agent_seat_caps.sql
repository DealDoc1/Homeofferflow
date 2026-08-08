-- Enforce brokerage agent-seat capacity for both pending invitations and
-- active memberships. Application checks give a friendly early error, but a
-- database trigger is necessary to prevent two concurrent requests from
-- oversubscribing the same brokerage.

begin;

create or replace function public.hof_enforce_agent_seat_cap()
returns trigger
language plpgsql
set search_path = public
as $$
declare
  cap integer;
  active_agents integer;
  pending_invites integer;
begin
  if new.role <> 'agent' then
    return new;
  end if;

  if tg_table_name = 'hof_brokerage_members' and new.status <> 'active' then
    return new;
  end if;
  if tg_table_name = 'hof_brokerage_invites' and new.status <> 'pending' then
    return new;
  end if;

  -- Serialize capacity decisions per brokerage. A null cap means the
  -- brokerage is intentionally uncapped.
  select user_cap into cap
  from public.hof_brokerages
  where id = new.brokerage_id
  for update;

  if cap is null then
    return new;
  end if;
  if cap < 0 then
    raise exception 'Brokerage has an invalid agent-seat limit.';
  end if;

  select count(*) into active_agents
  from public.hof_brokerage_members
  where brokerage_id = new.brokerage_id
    and role = 'agent'
    and status = 'active'
    and (tg_table_name <> 'hof_brokerage_members' or id <> new.id);

  select count(*) into pending_invites
  from public.hof_brokerage_invites
  where brokerage_id = new.brokerage_id
    and role = 'agent'
    and status = 'pending'
    and (tg_table_name <> 'hof_brokerage_invites' or id <> new.id)
    -- While accepting an email-matched invitation, do not double-count the
    -- invitation that is about to be marked accepted in the same workflow.
    and (tg_table_name <> 'hof_brokerage_members' or lower(email) <> lower(new.email));

  if active_agents + pending_invites >= cap then
    raise exception 'Brokerage agent-seat limit (%) has been reached.', cap
      using errcode = 'check_violation';
  end if;

  return new;
end;
$$;

drop trigger if exists hof_brokerage_invites_enforce_agent_seat_cap on public.hof_brokerage_invites;
create trigger hof_brokerage_invites_enforce_agent_seat_cap
before insert or update of brokerage_id, email, role, status
on public.hof_brokerage_invites
for each row execute function public.hof_enforce_agent_seat_cap();

drop trigger if exists hof_brokerage_members_enforce_agent_seat_cap on public.hof_brokerage_members;
create trigger hof_brokerage_members_enforce_agent_seat_cap
before insert or update of brokerage_id, email, role, status
on public.hof_brokerage_members
for each row execute function public.hof_enforce_agent_seat_cap();

commit;

-- Verification after applying:
-- select tgname, tgrelid::regclass
-- from pg_trigger
-- where tgname in (
--   'hof_brokerage_invites_enforce_agent_seat_cap',
--   'hof_brokerage_members_enforce_agent_seat_cap'
-- );


