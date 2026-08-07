-- Secure, expiring seller review links for private seller-disclosure review.
-- The raw token is never stored. This table is intentionally service-role
-- managed because the review page is public-by-token and must not expose the
-- draft table through the Data API.

begin;

create table if not exists public.hof_seller_disclosure_review_links (
  id uuid primary key default gen_random_uuid(),
  draft_id uuid not null references public.hof_seller_disclosure_drafts(id) on delete cascade,
  brokerage_id uuid not null references public.hof_brokerages(id) on delete restrict,
  agent_user_id uuid not null references auth.users(id) on delete cascade,
  token_hash text not null unique,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  viewed_at timestamptz,
  seller_attested_at timestamptz,
  seller_attested_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
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
