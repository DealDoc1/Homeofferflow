-- Targeted indexes for active workflow foreign keys reported by Supabase
-- advisors. These improve joins/filtering only; they do not alter RLS,
-- grants, or the data exposed to any role.

create index if not exists hof_ai_offer_reviews_user_id_idx
  on public.hof_ai_offer_reviews (user_id);

create index if not exists hof_brokerage_members_txr_agent_attested_by_idx
  on public.hof_brokerage_members (txr_agent_attested_by);

create index if not exists hof_listing_workspaces_seller_lead_id_idx
  on public.hof_listing_workspaces (seller_lead_id);

create index if not exists hof_seller_disclosure_drafts_disclosure_source_id_idx
  on public.hof_seller_disclosure_drafts (disclosure_source_id);

create index if not exists hof_seller_disclosure_drafts_listing_workspace_id_idx
  on public.hof_seller_disclosure_drafts (listing_workspace_id);

create index if not exists hof_seller_disclosure_drafts_seller_review_attested_by_idx
  on public.hof_seller_disclosure_drafts (seller_review_attested_by);

create index if not exists hof_seller_disclosure_drafts_water_source_id_idx
  on public.hof_seller_disclosure_drafts (water_source_id);

create index if not exists hof_seller_disclosure_review_links_agent_user_id_idx
  on public.hof_seller_disclosure_review_links (agent_user_id);

create index if not exists hof_seller_disclosure_review_links_brokerage_id_idx
  on public.hof_seller_disclosure_review_links (brokerage_id);

create index if not exists hof_seller_leads_brokerage_id_idx
  on public.hof_seller_leads (brokerage_id);

create index if not exists hof_seller_leads_user_id_idx
  on public.hof_seller_leads (user_id);

create index if not exists hof_standalone_agreements_form_source_id_idx
  on public.hof_standalone_agreements (form_source_id);

create index if not exists hof_usage_events_offer_id_idx
  on public.hof_usage_events (offer_id);
