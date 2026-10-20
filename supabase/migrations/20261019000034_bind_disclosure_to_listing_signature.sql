-- Coordinate with combined-packet code. No permission expansion or new queue.
begin;
set local lock_timeout = '5s';
alter table public.hof_seller_disclosure_drafts add column signature_packet_id uuid
  references public.hof_standalone_agreements(id) on delete restrict;
create index hof_seller_disclosure_packet_idx on public.hof_seller_disclosure_drafts(signature_packet_id)
  where signature_packet_id is not null;

create function public.hof_keep_packet_disclosure()
returns trigger language plpgsql security invoker set search_path=pg_catalog
as $$
begin
  if tg_op='DELETE' then
    if old.signature_packet_id is not null then
      raise exception using errcode='55000',message='Retain the disclosure included in this signing packet.';
    end if;
    return old;
  end if;
  if tg_op='INSERT' then
    if new.signature_packet_id is not null then
      raise exception using errcode='42501',message='Prepare the disclosure before including it in a signing packet.';
    end if;
    return new;
  end if;
  if new.signature_packet_id is not null and nullif(to_jsonb(new)->>'signature_offer_id','') is not null then
    raise exception using errcode='55000',message='This disclosure already belongs to another signing package.';
  end if;
  if old.signature_packet_id is not null and row(new.signature_packet_id,new.agent_user_id,new.brokerage_id,
    new.review_content_revision,new.seller_review_attested,new.seller_review_attested_at,
    new.seller_review_attested_by,new.seller_review_render_revision,new.signwell_document_id,
    new.response_data->'_hof_signature_delivery') is distinct from row(old.signature_packet_id,old.agent_user_id,old.brokerage_id,
    old.review_content_revision,old.seller_review_attested,old.seller_review_attested_at,
    old.seller_review_attested_by,old.seller_review_render_revision,old.signwell_document_id,
    old.response_data->'_hof_signature_delivery') then
    raise exception using errcode='55000',message='This disclosure is included in a signing packet. Create a new draft to change it.';
  end if;
  if new.signature_packet_id is distinct from old.signature_packet_id
    and (current_user in ('anon','authenticated') or pg_trigger_depth()<2) then
    raise exception using errcode='42501',message='Only the signing service can include a disclosure in a packet.';
  end if;
  return new;
end;
$$;
-- PostgreSQL fires same-kind row triggers alphabetically: the existing
-- content guard rotates its revision first, then this guard detects changes.
create trigger hof_packet_disclosure_lock before insert or update or delete on public.hof_seller_disclosure_drafts
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
    or new.agent_user_id is distinct from old.agent_user_id
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
    or nullif(to_jsonb(disclosure)->>'signature_offer_id','') is not null
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

-- Share the same parent-row lock as purchase signing and questionnaire saves.
-- Routine view/session timestamps do not change the proof and need no lock.
create function public.hof_keep_listing_disclosure_review()
returns trigger language plpgsql security invoker set search_path=pg_catalog
as $$
declare
  disclosure public.hof_seller_disclosure_drafts%rowtype;
begin
  if tg_op='UPDATE' and row(new.draft_id,new.agent_user_id,new.brokerage_id,new.seller_index,new.seller_name,new.seller_email,
    new.seller_attested_at,new.seller_attested_name,new.review_content_revision,new.review_render_revision,new.revoked_at)
    is not distinct from row(old.draft_id,old.agent_user_id,old.brokerage_id,old.seller_index,old.seller_name,old.seller_email,
    old.seller_attested_at,old.seller_attested_name,old.review_content_revision,old.review_render_revision,old.revoked_at) then
    return new;
  end if;
  select * into disclosure from public.hof_seller_disclosure_drafts d
    where d.id=case when tg_op='DELETE' then old.draft_id else new.draft_id end for update;
  if disclosure.signature_packet_id is not null then
    raise exception using errcode='55000',message='Retain the seller review used by this signing packet.';
  end if;
  return case when tg_op='DELETE' then old else new end;
end;
$$;
create trigger hof_listing_disclosure_review_guard before insert or update or delete on public.hof_seller_disclosure_review_links
  for each row execute function public.hof_keep_listing_disclosure_review();
revoke all on function public.hof_keep_listing_disclosure_review() from public,anon,authenticated;
grant execute on function public.hof_keep_listing_disclosure_review() to service_role;
-- Extend, never replace, the already applied production readiness contracts.
create function public.hof_listing_package_schema_readiness()
returns jsonb language plpgsql stable security invoker set search_path=pg_catalog
as $$
declare
  baseline jsonb;
  missing text[];
  constraint_definition text;
  required_trigger text;
begin
  baseline := public.hof_seller_disclosure_schema_readiness();
  select coalesce(array_agg(value),array[]::text[]) into missing
    from jsonb_array_elements_text(coalesce(baseline->'missing','[]'::jsonb)) as value;
  if baseline->>'contract' is distinct from 'homeofferflow-release-schema-v2' then
    missing := array_append(missing,'contract:disclosure-v2');
  end if;
  if baseline->'ready' is distinct from 'true'::jsonb and cardinality(missing)=0 then
    missing := array_append(missing,'baseline:not-ready');
  end if;
  select pg_get_constraintdef(c.oid) into constraint_definition from pg_constraint c
    where c.conrelid=to_regclass('public.hof_standalone_agreements')
      and c.conname='hof_standalone_agreements_form_code_check' and c.contype='c';
  if constraint_definition is null or strpos(constraint_definition,quote_literal('TXR-1101'))=0 then
    missing := array_append(missing,'form_code:hof_standalone_agreements.TXR-1101');
  end if;
  if not exists(select 1 from information_schema.columns where table_schema='public'
      and table_name='hof_seller_disclosure_drafts' and column_name='signature_packet_id') then
    missing := array_append(missing,'column:hof_seller_disclosure_drafts.signature_packet_id');
  end if;
  foreach required_trigger in array array['hof_packet_disclosure_lock','hof_listing_disclosure_signature_guard','hof_listing_disclosure_review_guard'] loop
    if not exists(select 1 from pg_trigger t join pg_class c on c.oid=t.tgrelid
      join pg_namespace n on n.oid=c.relnamespace where n.nspname='public'
      and c.relname=case required_trigger when 'hof_packet_disclosure_lock' then 'hof_seller_disclosure_drafts'
        when 'hof_listing_disclosure_review_guard' then 'hof_seller_disclosure_review_links' else 'hof_standalone_agreements' end
      and t.tgname=required_trigger and not t.tgisinternal and t.tgenabled in ('O','A')) then
      missing := array_append(missing,'trigger:'||required_trigger);
    end if;
  end loop;
  return jsonb_build_object('contract','homeofferflow-release-schema-v3',
    'ready',cardinality(missing)=0,'missing',to_jsonb(missing));
end;
$$;
revoke all on function public.hof_listing_package_schema_readiness() from public,anon,authenticated;
grant execute on function public.hof_listing_package_schema_readiness() to service_role;
notify pgrst,'reload schema';
commit;
