-- Record the review engine mode separately from review content. This lets
-- platform metrics distinguish live-model availability from a safe rules
-- fallback without loading any user review text.
alter table public.hof_ai_offer_reviews
  add column if not exists review_mode text;

alter table public.hof_ai_offer_reviews
  drop constraint if exists hof_ai_offer_reviews_review_mode_check;

alter table public.hof_ai_offer_reviews
  add constraint hof_ai_offer_reviews_review_mode_check
  check (review_mode is null or review_mode in ('live_ai', 'rules_fallback'));
