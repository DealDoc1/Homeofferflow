-- Permit a fresh seller-review credential only after the previous incomplete
-- credential is retired. Completed attestations remain immutable history.
begin;

drop index if exists public.hof_seller_review_links_draft_seller_idx;

create unique index if not exists hof_seller_review_links_draft_seller_active_idx
  on public.hof_seller_disclosure_review_links (draft_id, seller_index)
  where seller_index is not null
    and revoked_at is null
    and seller_attested_at is null;

commit;
