-- Server-only Stripe webhook ledger.
--
-- Stores delivery metadata only. It intentionally does not persist full Stripe
-- event bodies, billing details, card data, or customer-facing offer content.
-- The unique Stripe event ID lets the webhook acknowledge retried deliveries
-- without replaying events that already finished processing.

create table if not exists public.hof_stripe_webhook_events (
  id uuid primary key default gen_random_uuid(),
  stripe_event_id text not null unique,
  event_type text not null,
  livemode boolean not null,
  stripe_subscription_id text,
  stripe_customer_id text,
  processing_state text not null default 'received'
    check (processing_state in ('received', 'processed', 'ignored', 'failed')),
  error_code text,
  received_at timestamptz not null default now(),
  processed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists hof_stripe_webhook_events_received_at_idx
  on public.hof_stripe_webhook_events(received_at desc);
create index if not exists hof_stripe_webhook_events_state_received_idx
  on public.hof_stripe_webhook_events(processing_state, received_at desc);
create index if not exists hof_stripe_webhook_events_subscription_idx
  on public.hof_stripe_webhook_events(stripe_subscription_id)
  where stripe_subscription_id is not null;

alter table public.hof_stripe_webhook_events enable row level security;

revoke all on table public.hof_stripe_webhook_events from anon, authenticated;
grant all on table public.hof_stripe_webhook_events to service_role;

drop policy if exists "stripe_webhook_events_server_only" on public.hof_stripe_webhook_events;
create policy "stripe_webhook_events_server_only"
on public.hof_stripe_webhook_events
for all to authenticated
using (false)
with check (false);
