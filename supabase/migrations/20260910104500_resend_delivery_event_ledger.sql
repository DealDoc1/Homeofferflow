create table if not exists public.hof_resend_webhook_events (
  id uuid primary key default gen_random_uuid(),
  svix_id text not null unique,
  event_type text not null,
  delivery_status text not null check (delivery_status in ('sent', 'delivered', 'bounced', 'complained', 'suppressed', 'opened', 'clicked', 'other')),
  resend_email_id text,
  tags jsonb not null default '{}'::jsonb,
  processing_state text not null default 'received' check (processing_state in ('received', 'processed', 'ignored', 'failed')),
  event_created_at timestamptz,
  received_at timestamptz not null default now(),
  processed_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists hof_resend_webhook_events_received_at_idx
  on public.hof_resend_webhook_events(received_at desc);
create index if not exists hof_resend_webhook_events_status_received_idx
  on public.hof_resend_webhook_events(delivery_status, received_at desc);
create index if not exists hof_resend_webhook_events_type_received_idx
  on public.hof_resend_webhook_events(event_type, received_at desc);

alter table public.hof_resend_webhook_events enable row level security;

revoke all on table public.hof_resend_webhook_events from anon, authenticated;
grant all on table public.hof_resend_webhook_events to service_role;

drop policy if exists resend_webhook_events_server_only on public.hof_resend_webhook_events;
create policy resend_webhook_events_server_only
  on public.hof_resend_webhook_events
  for all to authenticated
  using (false)
  with check (false);
