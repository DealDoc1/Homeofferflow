-- Add the provider lifecycle to the existing agent-owned seller disclosure.
-- Browser users can continue to save and review a draft, but only the server
-- can mark a packet sent or signed after talking to SignWell.
begin;

alter table public.hof_seller_disclosure_drafts
  add column if not exists signwell_document_id text,
  add column if not exists signwell_status text,
  add column if not exists sent_at timestamptz,
  add column if not exists signed_at timestamptz;

alter table public.hof_seller_disclosure_drafts
  drop constraint if exists hof_seller_disclosure_drafts_status_check;

alter table public.hof_seller_disclosure_drafts
  add constraint hof_seller_disclosure_drafts_status_check
  check (status in ('draft', 'ready_for_review', 'sent', 'signed', 'void'));

create unique index if not exists hof_seller_disclosure_drafts_signwell_document_id_key
  on public.hof_seller_disclosure_drafts (signwell_document_id)
  where signwell_document_id is not null;

drop policy if exists hof_seller_disclosure_drafts_update_own
  on public.hof_seller_disclosure_drafts;
create policy hof_seller_disclosure_drafts_update_own
  on public.hof_seller_disclosure_drafts for update to authenticated
  using (
    (select auth.uid()) = agent_user_id
    and status in ('draft', 'ready_for_review')
  )
  with check (
    (select auth.uid()) = agent_user_id
    and status in ('draft', 'ready_for_review')
  );

commit;
