-- Track a real return from the Stripe cancellation URL without collecting
-- browser identity or partner content.  The per-checkout nonce prevents an
-- arbitrary lead ID from being used to manufacture funnel activity.
alter table public.hof_partner_leads
  add column if not exists checkout_returned_at timestamptz,
  add column if not exists checkout_resume_token uuid;

create index if not exists hof_partner_leads_checkout_returned_at_idx
  on public.hof_partner_leads (checkout_returned_at desc)
  where checkout_returned_at is not null;
