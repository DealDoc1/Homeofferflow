-- Additive, coordinated with the purchase-disclosure sender. No grants widened.
begin;
set local lock_timeout = '5s';

alter table public.hof_seller_disclosure_drafts add column signature_offer_id uuid
  references public.hof_offers(id) on delete restrict;
create index hof_seller_disclosure_offer_idx on public.hof_seller_disclosure_drafts(signature_offer_id)
  where signature_offer_id is not null;

create function public.hof_keep_purchase_disclosure()
returns trigger language plpgsql security invoker set search_path=pg_catalog
as $$
begin
  if tg_op='DELETE' then
    if old.signature_offer_id is not null then
      raise exception using errcode='55000',message='Retain the disclosure included in this signing offer.';
    end if;
    return old;
  end if;
  if tg_op='INSERT' then
    if new.signature_offer_id is not null then
      raise exception using errcode='42501',message='Prepare the disclosure before including it in an offer.';
    end if;
    return new;
  end if;
  if new.signature_offer_id is not null
    and nullif(to_jsonb(new)->>'signature_packet_id','') is not null then
    raise exception using errcode='55000',message='This disclosure already belongs to another signing package.';
  end if;
  if old.signature_offer_id is not null and row(new.signature_offer_id,new.agent_user_id,
    new.brokerage_id,new.review_content_revision,new.seller_review_attested,new.seller_review_attested_at,
    new.seller_review_attested_by,new.seller_review_render_revision,new.signwell_document_id,
    new.response_data->'_hof_signature_delivery') is distinct from row(old.signature_offer_id,old.agent_user_id,
    old.brokerage_id,old.review_content_revision,old.seller_review_attested,old.seller_review_attested_at,
    old.seller_review_attested_by,old.seller_review_render_revision,old.signwell_document_id,
    old.response_data->'_hof_signature_delivery') then
    raise exception using errcode='55000',message='This disclosure is included in a signing offer. Create a new draft to change it.';
  end if;
  if new.signature_offer_id is distinct from old.signature_offer_id
    and (current_user in ('anon','authenticated') or pg_trigger_depth()<2) then
    raise exception using errcode='42501',message='Only the saved offer signing checkpoint can include a disclosure.';
  end if;
  return new;
end;
$$;
create trigger hof_offer_disclosure_lock before insert or update or delete on public.hof_seller_disclosure_drafts
  for each row execute function public.hof_keep_purchase_disclosure();

create function public.hof_keep_purchase_disclosure_review()
returns trigger language plpgsql security invoker set search_path=pg_catalog
as $$
declare
  draft public.hof_seller_disclosure_drafts%rowtype;
  draft_id uuid;
begin
  draft_id := case when tg_op='DELETE' then old.draft_id else new.draft_id end;
  -- Parent row is the common lock for edits, attestations, retirement and send.
  -- No provider call occurs while this transaction is open.
  select * into draft from public.hof_seller_disclosure_drafts d where d.id=draft_id for update;
  if draft.signature_offer_id is not null then
    if tg_op in ('INSERT','DELETE') then
      raise exception using errcode='55000',message='Retain the seller review used by this signing offer.';
    end if;
    if row(new.draft_id,new.agent_user_id,new.brokerage_id,new.seller_index,new.seller_name,new.seller_email,
      new.seller_attested_at,new.seller_attested_name,new.review_content_revision,new.review_render_revision,new.revoked_at)
      is distinct from row(old.draft_id,old.agent_user_id,old.brokerage_id,old.seller_index,old.seller_name,old.seller_email,
      old.seller_attested_at,old.seller_attested_name,old.review_content_revision,old.review_render_revision,old.revoked_at) then
      raise exception using errcode='55000',message='Retain the reviewed seller and destination used by this signing offer.';
    end if;
  end if;
  return case when tg_op='DELETE' then old else new end;
end;
$$;
create trigger hof_purchase_disclosure_review_guard before insert or update or delete on public.hof_seller_disclosure_review_links
  for each row execute function public.hof_keep_purchase_disclosure_review();

create function public.hof_bind_purchase_disclosure()
returns trigger language plpgsql security invoker set search_path=pg_catalog
as $$
declare
  binding jsonb;
  prior_binding jsonb;
  journal jsonb;
  recipients jsonb;
  disclosure public.hof_seller_disclosure_drafts%rowtype;
  seller_names jsonb;
  seller record;
  buyer record;
  normalized_address text;
  full_address text;
  seller_count integer;
  buyer_count integer;
begin
  journal := new.offer_data->'_hof_signature_delivery';
  binding := journal->'seller_disclosure';
  if tg_op='INSERT' then
    if binding is not null then
      raise exception using errcode='42501',message='Save the offer before including its reviewed disclosure.';
    end if;
    return new;
  end if;
  prior_binding := old.offer_data->'_hof_signature_delivery'->'seller_disclosure';
  if prior_binding is not null and (binding is distinct from prior_binding
    or new.user_id is distinct from old.user_id or new.signwell_document_id is distinct from old.signwell_document_id) then
    raise exception using errcode='55000',message='Retain the disclosure attached to this signing offer.';
  end if;
  if binding is null then return new; end if;
  if prior_binding is not null then return new; end if;
  if current_user in ('anon','authenticated') then
    raise exception using errcode='42501',message='Only the signing service can include a reviewed disclosure.';
  end if;
  if binding->>'offer_id' is distinct from new.id::text or binding->>'user_id' is distinct from new.user_id::text
    or binding->>'fingerprint' is null or binding->>'fingerprint' !~ '^[a-f0-9]{64}$'
    or nullif(new.signwell_document_id,'') is null or journal->>'document_id' is distinct from new.signwell_document_id
    or journal->>'phase' not in ('prepared','sending') or journal->>'phase' is null then
    raise exception using errcode='55000',message='The saved signing request does not match this offer.';
  end if;
  select * into disclosure from public.hof_seller_disclosure_drafts d
    where d.id=(binding->>'id')::uuid and d.agent_user_id=new.user_id for update;
  if not found or disclosure.status <> 'draft' or disclosure.signwell_document_id is not null
    or disclosure.response_data ? '_hof_signature_delivery'
    or nullif(to_jsonb(disclosure)->>'signature_packet_id','') is not null
    or disclosure.signature_offer_id is not null
    or disclosure.review_content_revision::text is distinct from binding->>'revision'
    or disclosure.seller_review_render_revision is distinct from binding->>'render_revision'
    or not disclosure.seller_review_attested
    or new.offer_data->>'purchaseSellerDisclosureId' is distinct from disclosure.id::text
    or jsonb_array_length(disclosure.buyer_names)<>0 then
    raise exception using errcode='55000',message='The disclosure changed. Review the latest package before sending.';
  end if;
  seller_names := jsonb_build_array(coalesce(nullif(btrim(new.offer_data->>'seller1Name'),''),
    nullif(btrim(new.offer_data->>'seller1'),''),nullif(btrim(new.offer_data->>'seller'),'')));
  if coalesce(nullif(btrim(new.offer_data->>'seller2Name'),''),nullif(btrim(new.offer_data->>'seller2'),'')) is not null then
    seller_names := seller_names || jsonb_build_array(coalesce(nullif(btrim(new.offer_data->>'seller2Name'),''),new.offer_data->>'seller2'));
  end if;
  seller_count := jsonb_array_length(seller_names);
  recipients := journal->'recipients';
  buyer_count := case when nullif(btrim(new.offer_data->>'buyer2Email'),'') is null then 1 else 2 end;
  normalized_address := btrim(regexp_replace(lower(disclosure.property_address),'[^[:alnum:]_]+',' ','g'));
  full_address := concat_ws(' ',new.offer_data->>'address',new.offer_data->>'city',
    coalesce(nullif(new.offer_data->>'state',''),'TX'),new.offer_data->>'zip');
  if seller_count not between 1 and 2 or seller_count<>jsonb_array_length(disclosure.seller_names)
    or jsonb_typeof(recipients) is distinct from 'array' or jsonb_array_length(recipients)<>seller_count+buyer_count
    or nullif(normalized_address,'') is null
    or normalized_address not in (btrim(regexp_replace(lower(coalesce(new.offer_data->>'address','')),'[^[:alnum:]_]+',' ','g')),
      btrim(regexp_replace(lower(full_address),'[^[:alnum:]_]+',' ','g')))
    or (select count(distinct lower(btrim(value->>'email'))) from jsonb_array_elements(recipients)) <> seller_count+buyer_count
    or (select count(distinct value->>'id') from jsonb_array_elements(recipients)) <> seller_count+buyer_count then
    raise exception using errcode='55000',message='Confirm the property and every signing recipient before sending.';
  end if;
  for seller in select value as name,ordinality as idx from jsonb_array_elements_text(seller_names) with ordinality loop
    if nullif(btrim(seller.name),'') is null or
      (select count(*) from jsonb_array_elements_text(disclosure.seller_names) as s(name)
        where lower(regexp_replace(btrim(s.name),'\s+',' ','g'))=lower(regexp_replace(btrim(seller.name),'\s+',' ','g')))<>1
      or (select count(*) from public.hof_seller_disclosure_review_links l
        join lateral jsonb_array_elements(recipients) r on r->>'id'=(seller.idx+2)::text
        where l.draft_id=disclosure.id and l.agent_user_id=new.user_id and l.brokerage_id=disclosure.brokerage_id
          and l.seller_index between 1 and seller_count
          and lower(regexp_replace(btrim(disclosure.seller_names->>(l.seller_index-1)),'\s+',' ','g'))=lower(regexp_replace(btrim(seller.name),'\s+',' ','g'))
          and lower(regexp_replace(btrim(l.seller_name),'\s+',' ','g'))=lower(regexp_replace(btrim(seller.name),'\s+',' ','g'))
          and lower(regexp_replace(btrim(l.seller_attested_name),'\s+',' ','g'))=lower(regexp_replace(btrim(seller.name),'\s+',' ','g'))
          and lower(regexp_replace(btrim(r->>'name'),'\s+',' ','g'))=lower(regexp_replace(btrim(seller.name),'\s+',' ','g'))
          and nullif(btrim(l.seller_email),'') is not null and lower(btrim(l.seller_email))=lower(btrim(r->>'email'))
          and l.review_content_revision=disclosure.review_content_revision and l.review_render_revision=disclosure.seller_review_render_revision
          and l.revoked_at is null and l.seller_attested_at is not null)<>1 then
      raise exception using errcode='55000',message='Every seller must confirm these answers and signing details.';
    end if;
  end loop;
  for buyer in select * from (values
    ('1',new.offer_data->>'buyer1',new.offer_data->>'buyerEmail'),
    ('2',new.offer_data->>'buyer2',new.offer_data->>'buyer2Email')) as b(id,name,email)
    where id='1' or buyer_count=2 loop
    if nullif(btrim(buyer.name),'') is null or nullif(btrim(buyer.email),'') is null or
      (select count(*) from jsonb_array_elements(recipients) r where r->>'id'=buyer.id
        and lower(btrim(r->>'email'))=lower(btrim(buyer.email))
        and lower(regexp_replace(btrim(r->>'name'),'\s+',' ','g'))=lower(regexp_replace(btrim(buyer.name),'\s+',' ','g')))<>1 then
      raise exception using errcode='55000',message='Confirm each buyer name and signing email before sending.';
    end if;
  end loop;
  update public.hof_seller_disclosure_drafts set signature_offer_id=new.id where id=disclosure.id;
  return new;
end;
$$;
create trigger hof_purchase_disclosure_signature_guard before insert or update on public.hof_offers
  for each row execute function public.hof_bind_purchase_disclosure();
revoke all on function public.hof_keep_purchase_disclosure(),public.hof_keep_purchase_disclosure_review(),public.hof_bind_purchase_disclosure() from public,anon,authenticated;
grant execute on function public.hof_keep_purchase_disclosure(),public.hof_keep_purchase_disclosure_review(),public.hof_bind_purchase_disclosure() to service_role;
-- Independent additive contract: neither existing disclosure v2 nor listing
-- v3 readiness is replaced or made dependent on this unreleased work.
create function public.hof_purchase_disclosure_schema_readiness()
returns jsonb language plpgsql stable security invoker set search_path=pg_catalog
as $$
declare
  baseline jsonb;
  missing text[];
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
  if not exists(select 1 from information_schema.columns where table_schema='public'
    and table_name='hof_seller_disclosure_drafts' and column_name='signature_offer_id') then
    missing := array_append(missing,'column:hof_seller_disclosure_drafts.signature_offer_id');
  end if;
  foreach required_trigger in array array['hof_offer_disclosure_lock','hof_purchase_disclosure_review_guard','hof_purchase_disclosure_signature_guard'] loop
    if not exists(select 1 from pg_trigger t join pg_class c on c.oid=t.tgrelid
      join pg_namespace n on n.oid=c.relnamespace where n.nspname='public'
      and c.relname=case required_trigger when 'hof_offer_disclosure_lock' then 'hof_seller_disclosure_drafts'
        when 'hof_purchase_disclosure_review_guard' then 'hof_seller_disclosure_review_links' else 'hof_offers' end
      and t.tgname=required_trigger and not t.tgisinternal and t.tgenabled in ('O','A')) then
      missing := array_append(missing,'trigger:'||required_trigger);
    end if;
  end loop;
  return jsonb_build_object('contract','homeofferflow-purchase-disclosure-v1','ready',cardinality(missing)=0,'missing',to_jsonb(missing));
end;
$$;
revoke all on function public.hof_purchase_disclosure_schema_readiness() from public,anon,authenticated;
grant execute on function public.hof_purchase_disclosure_schema_readiness() to service_role;
notify pgrst,'reload schema';
commit;
