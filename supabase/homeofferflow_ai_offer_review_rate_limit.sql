-- HomeOfferFlow AI Offer Review rate limiting
--
-- This intentionally stores only a SHA-256 request key, never a raw IP
-- address or offer data. The RPC is server-only and atomically consumes an
-- hourly allowance before a paid Gemini request can begin.

begin;

create table if not exists public.hof_ai_offer_review_rate_limits (
  rate_key text not null check (rate_key ~ '^[a-f0-9]{64}$'),
  window_start timestamptz not null,
  request_count integer not null default 0 check (request_count >= 0),
  updated_at timestamptz not null default now(),
  primary key (rate_key, window_start)
);

alter table public.hof_ai_offer_review_rate_limits enable row level security;

revoke all on table public.hof_ai_offer_review_rate_limits from public, anon, authenticated;
grant select, insert, update, delete on table public.hof_ai_offer_review_rate_limits to service_role;

-- Deliberately deny browser roles even if future default grants change.
drop policy if exists hof_ai_offer_review_rate_limits_deny_browser on public.hof_ai_offer_review_rate_limits;
create policy hof_ai_offer_review_rate_limits_deny_browser
  on public.hof_ai_offer_review_rate_limits
  for all
  to anon, authenticated
  using (false)
  with check (false);

create or replace function public.hof_consume_ai_offer_review_rate_limit(
  p_key text,
  p_limit integer default 12
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  current_count integer;
  current_window timestamptz := pg_catalog.date_trunc('hour', pg_catalog.now());
begin
  if p_key is null or p_key !~ '^[a-f0-9]{64}$' then
    raise exception 'Invalid AI review rate-limit key';
  end if;

  if p_limit < 1 or p_limit > 100 then
    raise exception 'Invalid AI review rate-limit limit';
  end if;

  insert into public.hof_ai_offer_review_rate_limits (
    rate_key,
    window_start,
    request_count,
    updated_at
  )
  values (p_key, current_window, 1, pg_catalog.now())
  on conflict (rate_key, window_start)
  do update set
    request_count = public.hof_ai_offer_review_rate_limits.request_count + 1,
    updated_at = pg_catalog.now()
  returning request_count into current_count;

  return current_count <= p_limit;
end;
$$;

revoke all on function public.hof_consume_ai_offer_review_rate_limit(text, integer) from public, anon, authenticated;
grant execute on function public.hof_consume_ai_offer_review_rate_limit(text, integer) to service_role;

commit;
