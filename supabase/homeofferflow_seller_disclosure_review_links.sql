-- Email-verified seller review requests. No seller/property data is available
-- until the seller enters the one-time code delivered to seller_email.
begin;

create table if not exists public.hof_seller_disclosure_review_links (
  id uuid primary key default gen_random_uuid(),
  draft_id uuid not null references public.hof_seller_disclosure_drafts(id) on delete cascade,
  brokerage_id uuid not null references public.hof_brokerages(id) on delete restrict,
  agent_user_id uuid not null references auth.users(id) on delete cascade,
  seller_email text not null check (length(btrim(seller_email)) between 3 and 254),
  token_hash text not null unique,
  verification_code_hash text not null,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  viewed_at timestamptz,
  verified_at timestamptz,
  session_token_hash text unique,
  session_expires_at timestamptz,
  seller_attested_at timestamptz,
  seller_attested_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (
    (session_token_hash is null and session_expires_at is null)
    or
    (session_token_hash is not null and session_expires_at is not null)
  ),
  check (
    (seller_attested_at is null and seller_attested_name is null)
    or
    (seller_attested_at is not null and length(btrim(seller_attested_name)) between 1 and 180)
  )
);

create index if not exists hof_seller_review_links_draft_idx
  on public.hof_seller_disclosure_review_links (draft_id, created_at desc);

create index if not exists hof_seller_review_links_expiry_idx
  on public.hof_seller_disclosure_review_links (expires_at)
  where revoked_at is null and seller_attested_at is null;

alter table public.hof_seller_disclosure_review_links enable row level security;
revoke all on public.hof_seller_disclosure_review_links from anon;
revoke all on public.hof_seller_disclosure_review_links from authenticated;
grant all on public.hof_seller_disclosure_review_links to service_role;

commit;
