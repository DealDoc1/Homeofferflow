-- Coordinate with combined-packet code. No permission expansion or new queue.
begin;
alter table public.hof_seller_disclosure_drafts add column signature_packet_id uuid
  references public.hof_standalone_agreements(id) on delete restrict;
create index hof_seller_disclosure_packet_idx on public.hof_seller_disclosure_drafts(signature_packet_id)
  where signature_packet_id is not null;

create function public.hof_keep_packet_disclosure()
returns trigger language plpgsql security invoker set search_path=pg_catalog
as $$
begin
  if tg_op='INSERT' then
    if new.signature_packet_id is not null then
      raise exception using errcode='42501',message='Prepare the disclosure before including it in a signing packet.';
    end if;
    return new;
  end if;
  if old.signature_packet_id is not null and (
    new.signature_packet_id is distinct from old.signature_packet_id
    or new.review_content_revision is distinct from old.review_content_revision
    or new.signwell_document_id is distinct from old.signwell_document_id
    or (new.response_data -> '_hof_signature_delivery') is distinct from (old.response_data -> '_hof_signature_delivery')) then
    raise exception using errcode='55000',message='This disclosure is included in a signing packet. Create a new draft to change it.';
  end if;
  if new.signature_packet_id is distinct from old.signature_packet_id and current_user in ('anon','authenticated') then
    raise exception using errcode='42501',message='Only the signing service can include a disclosure in a packet.';
  end if;
  return new;
end;
$$;
-- PostgreSQL fires same-kind row triggers alphabetically: the existing
-- content guard rotates its revision first, then this guard detects changes.
create trigger hof_packet_disclosure_lock before insert or update on public.hof_seller_disclosure_drafts
  for each row execute function public.hof_keep_packet_disclosure();

create function public.hof_bind_listing_disclosure()
returns trigger language plpgsql security invoker set search_path=pg_catalog
as $$
declare
  binding jsonb;
  prior_binding jsonb;
  disclosure public.hof_seller_disclosure_drafts%rowtype;
begin
  prior_binding := old.agreement_data -> '_hof_signature_delivery' -> 'seller_disclosure';
  binding := new.agreement_data -> '_hof_signature_delivery' -> 'seller_disclosure';
  if prior_binding is not null and (binding is distinct from prior_binding
    or new.form_code is distinct from old.form_code
    or new.signwell_document_id is distinct from old.signwell_document_id) then
    raise exception using errcode='55000',message='Retain the disclosure attached to this signature request.';
  end if;
  if binding is null then return new; end if;
  if current_user in ('anon','authenticated') or new.form_code <> 'TXR-1101' then
    raise exception using errcode='42501',message='Only the signing service can include a reviewed disclosure.';
  end if;
  select * into disclosure from public.hof_seller_disclosure_drafts d
    where d.id=(binding ->> 'id')::uuid and d.agent_user_id=new.agent_user_id for update;
  if not found or disclosure.status <> 'draft' or disclosure.signwell_document_id is not null
    or disclosure.response_data ? '_hof_signature_delivery'
    or (disclosure.signature_packet_id is not null and disclosure.signature_packet_id <> new.id)
    or disclosure.review_content_revision::text is distinct from binding ->> 'revision'
    or disclosure.seller_review_render_revision is distinct from binding ->> 'render_revision'
    or not disclosure.seller_review_attested or new.signwell_document_id is null
    or new.agreement_data ->> 'disclosure_draft_id' is distinct from disclosure.id::text
    or jsonb_array_length(disclosure.buyer_names) <> 0
    or jsonb_array_length(disclosure.seller_names) <> jsonb_array_length(new.client_names)
    or lower(regexp_replace(btrim(disclosure.property_address),'\s+',' ','g')) is distinct from
       lower(regexp_replace(btrim(coalesce(new.agreement_data ->> 'property_address','')),'\s+',' ','g'))
    or exists (select 1 from jsonb_array_elements_text(disclosure.seller_names) s(name)
       where not exists (select 1 from jsonb_array_elements_text(new.client_names) n(name)
         where lower(regexp_replace(btrim(n.name),'\s+',' ','g'))=lower(regexp_replace(btrim(s.name),'\s+',' ','g'))))
    or exists (select 1 from jsonb_array_elements_text(disclosure.seller_names) with ordinality s(name,idx)
       where not exists (select 1 from public.hof_seller_disclosure_review_links l
         where l.draft_id=disclosure.id and l.agent_user_id=disclosure.agent_user_id
           and l.brokerage_id=disclosure.brokerage_id and l.seller_index=s.idx
           and l.review_content_revision=disclosure.review_content_revision
           and l.review_render_revision=disclosure.seller_review_render_revision
           and l.revoked_at is null and l.seller_attested_at is not null
           and lower(regexp_replace(btrim(coalesce(l.seller_attested_name,'')),'\s+',' ','g'))=
               lower(regexp_replace(btrim(s.name),'\s+',' ','g')))) then
    raise exception using errcode='55000',message='The disclosure changed. Review the latest packet before sending.';
  end if;
  update public.hof_seller_disclosure_drafts set signature_packet_id=new.id where id=disclosure.id;
  return new;
end;
$$;
create trigger hof_listing_disclosure_signature_guard before update on public.hof_standalone_agreements
  for each row execute function public.hof_bind_listing_disclosure();
revoke all on function public.hof_keep_packet_disclosure(), public.hof_bind_listing_disclosure() from public,anon,authenticated;
grant execute on function public.hof_keep_packet_disclosure(), public.hof_bind_listing_disclosure() to service_role;
commit;
