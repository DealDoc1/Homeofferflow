-- Adds payment and onboarding state to the existing central founding-partner table.
-- Apply after homeofferflow_partner_leads.sql. No partner placements are changed.

alter table public.hof_partner_leads
  add column if not exists payment_status text not null default 'not_started'
    check (payment_status in ('not_started', 'checkout_started', 'paid', 'failed', 'refunded')),
  add column if not exists onboarding_status text not null default 'not_started'
    check (onboarding_status in ('not_started', 'ready', 'in_progress', 'complete')),
  add column if not exists stripe_checkout_session_id text,
  add column if not exists stripe_payment_intent_id text,
  add column if not exists stripe_customer_id text,
  add column if not exists stripe_subscription_id text,
  add column if not exists subscription_status text,
  add column if not exists current_period_end timestamptz,
  add column if not exists paid_at timestamptz;

create unique index if not exists hof_partner_leads_stripe_checkout_session_id_key
  on public.hof_partner_leads(stripe_checkout_session_id)
  where stripe_checkout_session_id is not null;

create unique index if not exists hof_partner_leads_stripe_subscription_id_key
  on public.hof_partner_leads(stripe_subscription_id)
  where stripe_subscription_id is not null;

create index if not exists hof_partner_leads_payment_onboarding_idx
  on public.hof_partner_leads(payment_status, onboarding_status, created_at desc);

comment on column public.hof_partner_leads.payment_status is
  'Stripe Checkout state for the founding-partner launch charge and 90-day trial subscription.';
