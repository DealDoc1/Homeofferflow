-- One private invitation can collect answers; immutable review rows still bind
-- to the exact answers and renderer the seller actually reviewed.
begin;
alter table public.hof_seller_disclosure_review_links
  add column questionnaire_enabled boolean not null default false;
-- Retain the existing one-pending-request-per-seller index. Immutable review
-- proof rows have seller_attested_at set, so they do not conflict with the
-- canonical questionnaire invitation. Reissuing retires that invitation first.
-- This is additive and does not require dropping a production index.
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
-- Add a service-only v2 wrapper; retain the released core readiness RPC.
create function public.hof_seller_disclosure_schema_readiness()
returns jsonb language plpgsql stable security invoker set search_path=pg_catalog
as $$
declare baseline jsonb; missing jsonb := '[]'::jsonb;
begin
  baseline := public.hof_release_schema_readiness();
  if jsonb_typeof(baseline -> 'missing') = 'array' then
    missing := baseline -> 'missing';
  end if;
  if baseline ->> 'contract' is distinct from 'homeofferflow-release-schema-v1'
    or baseline -> 'ready' is distinct from 'true'::jsonb
    or jsonb_typeof(baseline -> 'missing') is distinct from 'array' then
    missing := missing || jsonb_build_array('baseline:release_schema_readiness');
  end if;
  if to_regprocedure('public.hof_save_seller_questionnaire(text,uuid,text,jsonb,jsonb,text)') is null then
    missing := missing || jsonb_build_array('function:hof_save_seller_questionnaire');
  end if;
  if not exists (select 1 from information_schema.columns where table_schema='public'
    and table_name='hof_seller_disclosure_review_links' and column_name='questionnaire_enabled') then
    missing := missing || jsonb_build_array('column:hof_seller_disclosure_review_links.questionnaire_enabled');
  end if;
  if not exists (select 1 from information_schema.columns where table_schema='public'
    and table_name='hof_seller_disclosure_drafts' and column_name='review_content_revision') then
    missing := missing || jsonb_build_array('column:hof_seller_disclosure_drafts.review_content_revision');
  end if;
  return jsonb_build_object('contract','homeofferflow-release-schema-v2',
    'ready',missing='[]'::jsonb,'missing',missing);
end;
$$;
revoke all on function public.hof_seller_disclosure_schema_readiness() from public,anon,authenticated;
grant execute on function public.hof_seller_disclosure_schema_readiness() to service_role;
notify pgrst, 'reload schema';
commit;
