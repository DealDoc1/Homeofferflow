-- One private invitation can collect answers; immutable review rows still bind
-- to the exact answers and renderer the seller actually reviewed.
begin;
alter table public.hof_seller_disclosure_review_links
  add column questionnaire_enabled boolean not null default false;
drop index public.hof_seller_review_links_draft_seller_active_idx;
create unique index hof_seller_review_links_draft_seller_active_idx
  on public.hof_seller_disclosure_review_links (draft_id, seller_index)
  where seller_index is not null and revoked_at is null
    and seller_attested_at is null and not questionnaire_enabled;
create unique index hof_seller_questionnaire_active_idx
  on public.hof_seller_disclosure_review_links (draft_id, seller_index)
  where seller_index is not null and revoked_at is null and questionnaire_enabled;

create function public.hof_save_seller_questionnaire(
  p_session_hash text, p_expected_revision uuid, p_action text,
  p_answers jsonb, p_water_answers jsonb, p_render_revision text)
returns jsonb language plpgsql security invoker set search_path = pg_catalog
as $$
declare
  access_row public.hof_seller_disclosure_review_links%rowtype;
  draft public.hof_seller_disclosure_drafts%rowtype;
  v_draft_id uuid;
begin
  select l.draft_id into v_draft_id from public.hof_seller_disclosure_review_links l
    where l.session_token_hash = p_session_hash;
  -- Parent first: same ordering as the existing immutable review triggers.
  select * into draft from public.hof_seller_disclosure_drafts d where d.id = v_draft_id for update;
  select * into access_row from public.hof_seller_disclosure_review_links l
    where l.session_token_hash = p_session_hash for update;
  if access_row.id is null or not access_row.questionnaire_enabled
    or access_row.revoked_at is not null or access_row.expires_at <= clock_timestamp()
    or access_row.session_expires_at is null or access_row.session_expires_at <= clock_timestamp()
    or draft.id is null or draft.status <> 'draft' or draft.signwell_document_id is not null
    or draft.response_data ? '_hof_signature_delivery'
    or access_row.agent_user_id <> draft.agent_user_id or access_row.brokerage_id <> draft.brokerage_id
    or access_row.seller_index is null or access_row.seller_index not between 1 and jsonb_array_length(draft.seller_names)
    or lower(regexp_replace(btrim(coalesce(access_row.seller_name,'')), '\s+', ' ', 'g')) <>
      lower(regexp_replace(btrim(draft.seller_names ->> (access_row.seller_index - 1)), '\s+', ' ', 'g')) then
    raise exception using errcode='42501', message='This seller questionnaire is unavailable.';
  end if;
  if draft.review_content_revision is distinct from p_expected_revision then
    raise exception using errcode='40001', message='The disclosure changed. Reload the latest answers before continuing.';
  end if;
  if p_action = 'save' then
    if jsonb_typeof(p_answers) is distinct from 'object' or jsonb_typeof(p_water_answers) is distinct from 'object'
      or octet_length(p_answers::text) + octet_length(p_water_answers::text) > 250000
      or exists (select 1 from jsonb_object_keys(p_answers || p_water_answers) k where left(k,1)='_')
      or (draft.water_source_id is null and p_water_answers <> '{}'::jsonb) then
      raise exception using errcode='22023', message='Enter valid disclosure answers.';
    end if;
    update public.hof_seller_disclosure_drafts set response_data=p_answers, water_rights_data=p_water_answers
      where id=draft.id returning * into draft;
  elsif p_action = 'review' then
    if p_render_revision is null or length(p_render_revision) not between 1 and 200 then
      raise exception using errcode='22023', message='Review the completed disclosure first.';
    end if;
    if not exists (select 1 from public.hof_seller_disclosure_review_links l where l.draft_id=draft.id
      and l.seller_index=access_row.seller_index and l.revoked_at is null and l.seller_attested_at is not null
      and l.review_content_revision=draft.review_content_revision and l.review_render_revision=p_render_revision
      and l.seller_attested_name=access_row.seller_name) then
      update public.hof_seller_disclosure_review_links set revoked_at=clock_timestamp()
        where draft_id=draft.id and seller_index=access_row.seller_index and revoked_at is null
          and seller_attested_at is null and not questionnaire_enabled;
      insert into public.hof_seller_disclosure_review_links
        (draft_id,brokerage_id,agent_user_id,seller_email,seller_name,seller_index,token_hash,
         verification_code_hash,expires_at,review_content_revision,review_render_revision,
         seller_attested_at,seller_attested_name)
        values (draft.id,draft.brokerage_id,draft.agent_user_id,access_row.seller_email,access_row.seller_name,
          access_row.seller_index,replace(gen_random_uuid()::text,'-','') || replace(gen_random_uuid()::text,'-',''),
          access_row.verification_code_hash,access_row.expires_at,draft.review_content_revision,
          p_render_revision,clock_timestamp(),access_row.seller_name);
    end if;
  else
    raise exception using errcode='22023', message='Choose a valid questionnaire action.';
  end if;
  return jsonb_build_object('reviewContentRevision',draft.review_content_revision,'saved',true);
end;
$$;
revoke all on function public.hof_save_seller_questionnaire(text,uuid,text,jsonb,jsonb,text) from public,anon,authenticated;
grant execute on function public.hof_save_seller_questionnaire(text,uuid,text,jsonb,jsonb,text) to service_role;
create or replace function public.hof_release_schema_readiness()
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
  missing text[] := array[]::text[];
  protected_table text;
  form_code_definition text;
  supported_form_code text;
begin
  if pg_catalog.to_regclass('public.hof_agent_profile_aliases') is null then
    missing := pg_catalog.array_append(missing, 'table:hof_agent_profile_aliases');
  end if;
  if pg_catalog.to_regclass('public.hof_email_deliveries') is null then
    missing := pg_catalog.array_append(missing, 'table:hof_email_deliveries');
  end if;
  if pg_catalog.to_regclass('public.hof_packet_generations') is null then
    missing := pg_catalog.array_append(missing, 'table:hof_packet_generations');
  end if;
  if pg_catalog.to_regclass('public.hof_checkout_payloads') is null then
    missing := pg_catalog.array_append(missing, 'table:hof_checkout_payloads');
  end if;
  if not exists (
    select 1 from information_schema.columns where table_schema = 'public'
      and table_name = 'hof_usage_events' and column_name = 'generation_key'
  ) then
    missing := pg_catalog.array_append(missing, 'column:hof_usage_events.generation_key');
  end if;
  if pg_catalog.to_regprocedure('public.hof_claim_packet_generation(uuid,uuid,text,uuid)') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_claim_packet_generation');
  end if;
  if pg_catalog.to_regprocedure('public.hof_complete_packet_generation(uuid,text,uuid)') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_complete_packet_generation');
  end if;
  if pg_catalog.to_regprocedure('public.hof_release_unrendered_packet(uuid,text,uuid)') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_release_unrendered_packet');
  end if;
  if pg_catalog.to_regprocedure('public.hof_packet_usage_summary(uuid)') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_packet_usage_summary');
  end if;
  if pg_catalog.to_regprocedure('public.hof_preserve_email_delivery()') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_preserve_email_delivery');
  end if;
  if pg_catalog.to_regprocedure('public.hof_protect_offer_packet_autosave()') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_protect_offer_packet_autosave');
  end if;
  if pg_catalog.to_regprocedure('public.hof_preserve_checkout_payload()') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_preserve_checkout_payload');
  end if;
  foreach protected_table in array array[
    'hof_agent_profile_aliases', 'hof_email_deliveries', 'hof_packet_generations',
    'hof_checkout_payloads', 'hof_standalone_agreements', 'hof_brokerage_form_sources'
  ] loop
    if not exists (
      select 1 from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public' and c.relname = protected_table and c.relrowsecurity
    ) then
      missing := pg_catalog.array_append(missing, 'rls:' || protected_table);
    end if;
  end loop;
  if not exists (
    select 1 from pg_catalog.pg_trigger t
    join pg_catalog.pg_class c on c.oid = t.tgrelid
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relname = 'hof_offers'
      and t.tgname = 'hof_protect_offer_packet_autosave' and not t.tgisinternal
  ) then
    missing := pg_catalog.array_append(missing, 'trigger:hof_protect_offer_packet_autosave');
  end if;
  select pg_catalog.pg_get_constraintdef(c.oid) into form_code_definition
  from pg_catalog.pg_constraint c
  where c.conrelid = pg_catalog.to_regclass('public.hof_standalone_agreements')
    and c.conname = 'hof_standalone_agreements_form_code_check' and c.contype = 'c';
  foreach supported_form_code in array array['TXR-1101','TXR-1501','TXR-1506','TXR-1507','TXR-1508','TXR-1905','TXR-1914','TXR-1917','TXR-1919','TXR-1948','TXR-1953','TXR-1954','TREC-62-0','TREC-38-8','TREC-39-11'] loop
    if form_code_definition is null
      or pg_catalog.strpos(form_code_definition, pg_catalog.quote_literal(supported_form_code)) = 0 then
      missing := pg_catalog.array_append(missing, 'form_code:hof_standalone_agreements.' || supported_form_code);
    end if;
  end loop;
  if pg_catalog.to_regprocedure('public.hof_save_seller_questionnaire(text,uuid,text,jsonb,jsonb,text)') is null then
    missing := pg_catalog.array_append(missing, 'function:hof_save_seller_questionnaire');
  end if;
  if not exists (select 1 from information_schema.columns where table_schema='public'
    and table_name='hof_seller_disclosure_review_links' and column_name='questionnaire_enabled') then
    missing := pg_catalog.array_append(missing, 'column:hof_seller_disclosure_review_links.questionnaire_enabled');
  end if;
  if not exists (select 1 from information_schema.columns where table_schema='public'
    and table_name='hof_seller_disclosure_drafts' and column_name='review_content_revision') then
    missing := pg_catalog.array_append(missing, 'column:hof_seller_disclosure_drafts.review_content_revision');
  end if;
  return pg_catalog.jsonb_build_object(
    'contract', 'homeofferflow-release-schema-v2',
    'ready', coalesce(pg_catalog.array_length(missing, 1), 0) = 0,
    'missing', pg_catalog.to_jsonb(missing)
  );
end;
$$;
revoke all on function public.hof_release_schema_readiness() from public, anon, authenticated;
grant execute on function public.hof_release_schema_readiness() to service_role;
comment on function public.hof_release_schema_readiness() is
  'Service-only fail-closed contract checked immediately before the coordinated HomeOfferFlow production release.';
commit;
