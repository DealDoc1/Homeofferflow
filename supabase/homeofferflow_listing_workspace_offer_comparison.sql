-- Private seller-side offer comparison worksheet.
-- This stores agent-owned educational notes only; it does not create, send,
-- sign, or interpret a contract.

begin;

create table if not exists public.hof_listing_workspace_offers (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.hof_listing_workspaces(id) on delete cascade,
  agent_user_id uuid not null references auth.users(id) on delete cascade,
  offer_label text not null check (length(trim(offer_label)) between 1 and 120),
  offer_price numeric(14,2) check (offer_price is null or offer_price >= 0),
  financing_type text check (financing_type is null or length(trim(financing_type)) <= 80),
  seller_concessions numeric(14,2) check (seller_concessions is null or seller_concessions >= 0),
  closing_date date,
  option_days integer check (option_days is null or option_days between 0 and 365),
  contingency_notes text check (contingency_notes is null or length(contingency_notes) <= 2000),
  status text not null default 'received' check (status in ('received','reviewing','preferred','declined')),
  private_notes text check (private_notes is null or length(private_notes) <= 4000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.hof_listing_workspace_offers enable row level security;
revoke all on public.hof_listing_workspace_offers from anon;
grant select, insert, update, delete on public.hof_listing_workspace_offers to authenticated;

commit;
