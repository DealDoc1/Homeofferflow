-- Additive support for individually addressed seller review links.
-- This remains review-only; it does not activate signing or form delivery.
begin;

alter table public.hof_seller_disclosure_review_links
  add column if not exists seller_name text,
  add column if not exists seller_index smallint;

alter table public.hof_seller_disclosure_review_links
  drop constraint if exists hof_seller_review_links_seller_name_check;

alter table public.hof_seller_disclosure_review_links
  add constraint hof_seller_review_links_seller_name_check
  check (seller_name is null or length(btrim(seller_name)) between 1 and 180);

alter table public.hof_seller_disclosure_review_links
  drop constraint if exists hof_seller_review_links_seller_index_check;

alter table public.hof_seller_disclosure_review_links
  add constraint hof_seller_review_links_seller_index_check
  check (seller_index is null or seller_index between 1 and 2);

create unique index if not exists hof_seller_review_links_draft_seller_idx
  on public.hof_seller_disclosure_review_links (draft_id, seller_index)
  where seller_index is not null;

commit;
