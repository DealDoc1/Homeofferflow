-- Backend-only immutable email requests. Deploy this schema before the sender.
create table public.hof_email_deliveries (
  delivery_key text primary key check (delivery_key ~ '^hof-email-v1-[0-9a-f]{64}$'),
  payload jsonb,
  payload_fingerprint text not null check (payload_fingerprint ~ '^[0-9a-f]{64}$'),
  status text not null default 'pending' check (status in ('pending', 'accepted')),
  first_attempt_at double precision check (first_attempt_at between 0 and 253402300799),
  provider_id text,
  created_at timestamptz not null default now(),
  constraint hof_email_delivery_state check (
    (status = 'pending' and payload is not null and jsonb_typeof(payload) = 'object' and provider_id is null)
    or (status = 'accepted' and payload is null and provider_id is not null
        and length(btrim(provider_id)) > 0 and first_attempt_at is not null)
  )
);

alter table public.hof_email_deliveries enable row level security;
revoke all on table public.hof_email_deliveries from public, anon, authenticated, service_role;
grant select, insert, update on table public.hof_email_deliveries to service_role;

create function public.hof_preserve_email_delivery()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
begin
  if TG_OP = 'INSERT' then
    if NEW.status <> 'pending' or NEW.first_attempt_at is not null or NEW.provider_id is not null then
      raise exception 'Email delivery must begin as an unattempted request';
    end if;
    NEW.created_at := clock_timestamp();
  else
    if NEW.delivery_key is distinct from OLD.delivery_key
       or NEW.payload_fingerprint is distinct from OLD.payload_fingerprint
       or NEW.created_at is distinct from OLD.created_at then
      raise exception 'Email delivery identity is immutable';
    end if;
    if OLD.first_attempt_at is not null and NEW.first_attempt_at is distinct from OLD.first_attempt_at then
      raise exception 'Email delivery attempt time is immutable';
    end if;
    if OLD.status = 'accepted' and
       (NEW.status <> 'accepted' or NEW.provider_id is distinct from OLD.provider_id or NEW.payload is not null) then
      raise exception 'Email delivery acceptance is final';
    end if;
    if NEW.status = 'pending' and NEW.payload is distinct from OLD.payload then
      raise exception 'Pending email contents are immutable';
    end if;
    if NEW.status = 'accepted' and OLD.first_attempt_at is null then
      raise exception 'Email delivery must be attempted before acceptance';
    end if;
  end if;
  return NEW;
end;
$$;

revoke all on function public.hof_preserve_email_delivery() from public, anon, authenticated;
grant execute on function public.hof_preserve_email_delivery() to service_role;

create trigger hof_preserve_email_delivery
before insert or update on public.hof_email_deliveries
for each row execute function public.hof_preserve_email_delivery();

comment on table public.hof_email_deliveries is
  'Service-only transactional email outbox. Clear payload after provider acceptance; retain receipts to prevent checkout replay.';
