-- Apply before deploying the reference-based buyer checkout sender/receiver.
-- Exact serialized text preserves cross-language hashes and Unicode answers.
create table public.hof_checkout_payloads (
  id uuid primary key,
  payload_text text not null check (octet_length(payload_text) between 2 and 4194304),
  payload_sha256 text not null check (payload_sha256 ~ '^[0-9a-f]{64}$'),
  stripe_session_id text unique check (stripe_session_id ~ '^cs_[A-Za-z0-9_]+$'),
  created_at timestamptz not null default now()
);
alter table public.hof_checkout_payloads enable row level security;
revoke all on table public.hof_checkout_payloads from public, anon, authenticated, service_role;
grant select, insert on table public.hof_checkout_payloads to service_role;
grant update(stripe_session_id) on table public.hof_checkout_payloads to service_role;

create function public.hof_preserve_checkout_payload()
returns trigger language plpgsql security invoker set search_path = pg_catalog as $$
begin
  if TG_OP = 'INSERT' then
    if NEW.stripe_session_id is not null then
      raise exception 'Checkout payload must be saved before session binding';
    end if;
    NEW.created_at := clock_timestamp();
  elsif NEW.id is distinct from OLD.id
     or NEW.payload_text is distinct from OLD.payload_text
     or NEW.payload_sha256 is distinct from OLD.payload_sha256
     or NEW.created_at is distinct from OLD.created_at
     or (OLD.stripe_session_id is not null and NEW.stripe_session_id is distinct from OLD.stripe_session_id) then
    raise exception 'Checkout payload and its session binding are immutable';
  end if;
  return NEW;
end;
$$;
revoke all on function public.hof_preserve_checkout_payload() from public, anon, authenticated;
create trigger hof_preserve_checkout_payload
before insert or update on public.hof_checkout_payloads
for each row execute function public.hof_preserve_checkout_payload();
