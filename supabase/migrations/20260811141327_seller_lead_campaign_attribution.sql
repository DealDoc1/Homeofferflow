-- Retain a minimal, privacy-safe acquisition attribution record for public
-- FSBO requests. Only the standard UTM fields and a server-derived source are
-- stored: never a full landing URL, referrer, address, or other identity data.

begin;

alter table public.hof_seller_leads
  add column if not exists source text not null default 'website_fsbo_intake',
  add column if not exists utm_source text,
  add column if not exists utm_medium text,
  add column if not exists utm_campaign text,
  add column if not exists utm_content text;

alter table public.hof_seller_leads
  add constraint hof_seller_leads_source_allowed
    check (source in ('website_fsbo_intake', 'tracked_seller_landing')),
  add constraint hof_seller_leads_utm_source_length
    check (utm_source is null or char_length(utm_source) <= 120),
  add constraint hof_seller_leads_utm_medium_length
    check (utm_medium is null or char_length(utm_medium) <= 120),
  add constraint hof_seller_leads_utm_campaign_length
    check (utm_campaign is null or char_length(utm_campaign) <= 160),
  add constraint hof_seller_leads_utm_content_length
    check (utm_content is null or char_length(utm_content) <= 160);

create index if not exists hof_seller_leads_source_created_at_idx
  on public.hof_seller_leads (source, created_at desc);

commit;
