-- Deploy with the server generation integration and
-- retirement of browser-requested usage writes, never on its own.
alter table public.hof_usage_events add column if not exists generation_key text;
create unique index if not exists hof_usage_generation_key_unique
  on public.hof_usage_events(generation_key) where generation_key is not null;
create index if not exists hof_usage_packet_month_lookup
  on public.hof_usage_events(user_id, billing_month) where event_type = 'signed_packet';

create table public.hof_packet_generations (
  generation_key text primary key check (generation_key ~ '^hof-packet-v1-[0-9a-f]{64}$'),
  user_id uuid not null,
  offer_id uuid not null,
  answers_hash text not null check (answers_hash ~ '^[0-9a-f]{64}$'),
  billing_month text not null check (billing_month ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
  status text not null check (status in ('reserved','completed','released')),
  attempt_token uuid,
  lease_until timestamptz,
  usage_event_id uuid unique references public.hof_usage_events(id),
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  unique(user_id, offer_id, answers_hash),
  check (
    (status = 'reserved' and attempt_token is not null and lease_until is not null
       and usage_event_id is null and completed_at is null)
    or (status = 'completed' and attempt_token is null and lease_until is null
       and usage_event_id is not null and completed_at is not null)
    or (status = 'released' and attempt_token is null and lease_until is null
       and usage_event_id is null and completed_at is null)
  )
);
create index hof_packet_reservations_month_lookup
  on public.hof_packet_generations(user_id,billing_month) where status = 'reserved';
alter table public.hof_packet_generations enable row level security;
revoke all on public.hof_packet_generations from public, anon, authenticated, service_role;
grant select, insert, update on public.hof_packet_generations to service_role;

create function public.hof_claim_packet_generation(
  p_user uuid, p_offer uuid, p_answers_hash text, p_attempt uuid
) returns jsonb language plpgsql security invoker set search_path = pg_catalog as $$
declare
  v_subscription public.hof_subscriptions%rowtype;
  v_row public.hof_packet_generations%rowtype;
  v_key text;
  v_month text;
  v_used bigint;
  v_held bigint;
begin
  if p_user is null or p_offer is null or p_attempt is null or p_answers_hash is null
     or p_answers_hash !~ '^[0-9a-f]{64}$' then
    raise exception 'Invalid packet reservation';
  end if;
  -- Lock one authoritative subscription row. Every quota mutation below uses
  -- this same lock order; no PDF work or HTTP is inside the transaction.
  begin
    select * into strict v_subscription from public.hof_subscriptions
      where user_id = p_user for update;
  exception when no_data_found then
    return jsonb_build_object('outcome','no_subscription');
  end;
  perform 1 from public.hof_offers where id = p_offer and user_id = p_user for key share;
  if not found then return jsonb_build_object('outcome','not_owned'); end if;
  v_key := 'hof-packet-v1-' || encode(sha256(convert_to(
    p_user::text || ':' || p_offer::text || ':' || p_answers_hash, 'UTF8')), 'hex');
  select * into v_row from public.hof_packet_generations where generation_key = v_key for update;
  if found and v_row.status = 'completed' then
    return to_jsonb(v_row) || jsonb_build_object('outcome','completed');
  end if;
  -- Historical browser-created events have no trustworthy answer fingerprint.
  -- Do not charge that same offer again or invent a completed receipt for it.
  -- Its existing download/signature-retry routes remain the recovery path.
  if v_row.generation_key is null and exists (
    select 1 from public.hof_usage_events where user_id=p_user and offer_id=p_offer
      and event_type='signed_packet' and generation_key is null
  ) then
    return jsonb_build_object('outcome','legacy_packet');
  end if;
  if v_subscription.status not in ('beta','trialing','active','free_admin') then
    return jsonb_build_object('outcome','inactive');
  end if;
  if v_row.status = 'reserved' then
    if v_row.lease_until > clock_timestamp() and v_row.attempt_token <> p_attempt then
      return jsonb_build_object('outcome','busy');
    end if;
    -- Expiry permits recovery, not a free quota slot. Keep the original month.
    update public.hof_packet_generations set attempt_token = p_attempt,
      lease_until = clock_timestamp() + interval '5 minutes'
      where generation_key = v_key returning * into v_row;
    return to_jsonb(v_row) || jsonb_build_object('outcome','reserved');
  end if;
  v_month := to_char(clock_timestamp() at time zone 'UTC', 'YYYY-MM');
  select coalesce(sum(greatest(quantity,0)),0) into v_used from public.hof_usage_events
    where user_id = p_user and billing_month = v_month and event_type = 'signed_packet';
  select count(*) into v_held from public.hof_packet_generations
    where user_id = p_user and billing_month = v_month and status = 'reserved';
  if v_used + v_held >= greatest(0, least(coalesce(v_subscription.packet_limit,10),10000)) then
    return jsonb_build_object('outcome','limit_reached');
  end if;
  insert into public.hof_packet_generations(generation_key,user_id,offer_id,answers_hash,
    billing_month,status,attempt_token,lease_until)
    values(v_key,p_user,p_offer,p_answers_hash,v_month,'reserved',p_attempt,clock_timestamp()+interval '5 minutes')
    on conflict(generation_key) do update set status='reserved',billing_month=v_month,
      attempt_token=p_attempt,lease_until=clock_timestamp()+interval '5 minutes'
    returning * into v_row;
  return to_jsonb(v_row) || jsonb_build_object('outcome','reserved');
end;
$$;

create function public.hof_complete_packet_generation(p_user uuid, p_key text, p_attempt uuid)
returns jsonb language plpgsql security invoker set search_path = pg_catalog as $$
declare
  v_row public.hof_packet_generations%rowtype;
  v_usage uuid;
begin
  perform 1 from public.hof_subscriptions where user_id=p_user for update;
  select * into v_row from public.hof_packet_generations
    where generation_key=p_key and user_id=p_user for update;
  if not found then return jsonb_build_object('outcome','not_found'); end if;
  if v_row.status='completed' then
    return to_jsonb(v_row) || jsonb_build_object('outcome','completed');
  end if;
  if v_row.status<>'reserved' or p_attempt is null or v_row.attempt_token<>p_attempt then
    return jsonb_build_object('outcome','stale_attempt');
  end if;
  -- Call only after successful local rendering, before any outbound signing
  -- or document-email request. Completed retries consume no additional unit.
  insert into public.hof_usage_events(user_id,offer_id,event_type,quantity,billing_month,metadata,generation_key)
    values(p_user,v_row.offer_id,'signed_packet',1,v_row.billing_month,
      '{"source":"server_packet_generation"}'::jsonb,p_key)
    returning id into v_usage;
  update public.hof_packet_generations set status='completed',usage_event_id=v_usage,
    completed_at=clock_timestamp(),attempt_token=null,lease_until=null
    where generation_key=p_key returning * into v_row;
  return to_jsonb(v_row) || jsonb_build_object('outcome','completed');
end;
$$;

create function public.hof_release_unrendered_packet(p_user uuid, p_key text, p_attempt uuid)
returns boolean language plpgsql security invoker set search_path = pg_catalog as $$
declare v_changed integer;
begin
  -- Only a definite render failure may use this operation. A timeout after
  -- completion/outbound work must never release allowance or erase evidence.
  perform 1 from public.hof_subscriptions where user_id=p_user for update;
  update public.hof_packet_generations set status='released',attempt_token=null,lease_until=null
    where generation_key=p_key and user_id=p_user and status='reserved' and attempt_token=p_attempt;
  get diagnostics v_changed = row_count;
  return v_changed=1;
end;
$$;

revoke all on function public.hof_claim_packet_generation(uuid,uuid,text,uuid) from public, anon, authenticated;
revoke all on function public.hof_complete_packet_generation(uuid,text,uuid) from public, anon, authenticated;
revoke all on function public.hof_release_unrendered_packet(uuid,text,uuid) from public, anon, authenticated;
grant execute on function public.hof_claim_packet_generation(uuid,uuid,text,uuid) to service_role;
grant execute on function public.hof_complete_packet_generation(uuid,text,uuid) to service_role;
grant execute on function public.hof_release_unrendered_packet(uuid,text,uuid) to service_role;

-- One database snapshot prevents a completion moving from reserved to used
-- between separate reads. The browser supplies neither totals nor the month.
create function public.hof_packet_usage_summary(p_user uuid)
returns jsonb language sql stable security invoker set search_path = pg_catalog as $$
  select jsonb_build_object(
    'billingMonth', to_char(now() at time zone 'UTC', 'YYYY-MM'),
    'used', (select coalesce(sum(greatest(quantity,0)),0) from public.hof_usage_events
      where user_id=p_user and event_type='signed_packet'
      and billing_month=to_char(now() at time zone 'UTC', 'YYYY-MM')),
    'reserved', (select count(*) from public.hof_packet_generations where user_id=p_user
      and status='reserved' and billing_month=to_char(now() at time zone 'UTC', 'YYYY-MM')),
    'limit', coalesce((select greatest(0,least(coalesce(packet_limit,10),10000))
      from public.hof_subscriptions where user_id=p_user),0)
  );
$$;
revoke all on function public.hof_packet_usage_summary(uuid) from public, anon, authenticated;
grant execute on function public.hof_packet_usage_summary(uuid) to service_role;
