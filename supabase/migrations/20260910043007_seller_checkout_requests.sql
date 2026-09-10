-- Fixed-price seller packages can be paid only after a platform administrator
-- confirms the scope with the seller. Quote-based and licensed-provider
-- packages deliberately remain outside this checkout path.
alter table public.hof_seller_leads
  add column if not exists seller_checkout_status text not null default 'not_requested',
  add column if not exists seller_checkout_session_id text,
  add column if not exists seller_checkout_payment_intent_id text,
  add column if not exists seller_checkout_price_cents integer,
  add column if not exists seller_checkout_requested_at timestamptz,
  add column if not exists seller_checkout_paid_at timestamptz;

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'hof_seller_leads_checkout_status_allowed') then
    alter table public.hof_seller_leads add constraint hof_seller_leads_checkout_status_allowed
      check (seller_checkout_status in ('not_requested', 'sent', 'paid'));
  end if;
  if not exists (select 1 from pg_constraint where conname = 'hof_seller_leads_checkout_price_nonnegative') then
    alter table public.hof_seller_leads add constraint hof_seller_leads_checkout_price_nonnegative
      check (seller_checkout_price_cents is null or seller_checkout_price_cents >= 0);
  end if;
end $$;

create unique index if not exists hof_seller_leads_checkout_session_id_key
  on public.hof_seller_leads (seller_checkout_session_id)
  where seller_checkout_session_id is not null;
