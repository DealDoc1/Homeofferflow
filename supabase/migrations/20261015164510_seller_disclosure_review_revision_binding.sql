-- Coordinate with the content-bound seller-review API release. No backfilled
-- attestation: an old review without a version must not approve changed text.
begin;

alter table public.hof_seller_disclosure_drafts
  add column review_content_revision uuid not null default gen_random_uuid(),
  add column seller_review_render_revision text;
alter table public.hof_seller_disclosure_review_links
  add column review_content_revision uuid,
  add column review_render_revision text;

create function public.hof_guard_disclosure_review_content()
returns trigger language plpgsql security invoker set search_path = pg_catalog
as $$
declare
  content_changed boolean;
begin
  if tg_op = 'INSERT' then
    if new.seller_review_attested or new.seller_review_attested_at is not null
      or new.seller_review_attested_by is not null or new.seller_review_render_revision is not null then
      raise exception using errcode = '42501', message = 'A new disclosure requires seller review.';
    end if;
    new.review_content_revision := gen_random_uuid();
    return new;
  end if;
  if (old.signwell_document_id is not null and new.signwell_document_id is distinct from old.signwell_document_id)
    or (old.response_data ? '_hof_signature_delivery' and not new.response_data ? '_hof_signature_delivery') then
    raise exception using errcode = '55000', message = 'The saved signing request must be retained. Create a new draft for a replacement.';
  end if;
  content_changed := row(new.agent_user_id, new.brokerage_id, new.property_address,
    new.seller_names, new.buyer_names, new.disclosure_source_id, new.water_source_id,
    new.disclosure_source_revision, new.water_source_revision,
    new.response_data - '_hof_signature_delivery', new.water_rights_data)
    is distinct from row(old.agent_user_id, old.brokerage_id, old.property_address,
    old.seller_names, old.buyer_names, old.disclosure_source_id, old.water_source_id,
    old.disclosure_source_revision, old.water_source_revision,
    old.response_data - '_hof_signature_delivery', old.water_rights_data);
  if content_changed then
    if old.status <> 'draft' or old.signwell_document_id is not null
       or old.response_data ? '_hof_signature_delivery' then
      raise exception using errcode = '55000', message = 'This disclosure already has a signing request. Create a new draft to change its answers.';
    end if;
    new.review_content_revision := gen_random_uuid();
    new.seller_review_attested := false;
    new.seller_review_attested_at := null;
    new.seller_review_attested_by := null;
    new.seller_review_render_revision := null;
  else
    new.review_content_revision := old.review_content_revision;
  end if;
  new.updated_at := clock_timestamp();
  if new.seller_review_attested then
    if current_user in ('anon', 'authenticated') then
      if row(new.seller_review_attested, new.seller_review_attested_at,
         new.seller_review_attested_by, new.seller_review_render_revision)
         is distinct from row(old.seller_review_attested, old.seller_review_attested_at,
         old.seller_review_attested_by, old.seller_review_render_revision) then
        raise exception using errcode = '42501', message = 'Seller review must be completed through the private review request.';
      end if;
    else
      if new.seller_review_render_revision is null or exists (
        select 1 from jsonb_array_elements_text(new.seller_names) with ordinality as s(name, idx)
        where not exists (
          select 1 from public.hof_seller_disclosure_review_links l
          where l.draft_id = new.id and l.brokerage_id = new.brokerage_id
            and l.agent_user_id = new.agent_user_id and l.seller_index = s.idx
            and l.revoked_at is null and l.seller_attested_at is not null
            and l.review_content_revision = new.review_content_revision
            and l.review_render_revision = new.seller_review_render_revision
            and lower(regexp_replace(btrim(l.seller_name), '\s+', ' ', 'g')) = lower(regexp_replace(btrim(s.name), '\s+', ' ', 'g'))
            and lower(regexp_replace(btrim(l.seller_attested_name), '\s+', ' ', 'g')) = lower(regexp_replace(btrim(s.name), '\s+', ' ', 'g'))
        )
      ) then
        raise exception using errcode = '55000', message = 'Every seller must review the current disclosure before signing.';
      end if;
    end if;
  end if;
  return new;
end;
$$;

create function public.hof_guard_disclosure_review_link()
returns trigger language plpgsql security invoker set search_path = pg_catalog
as $$
declare
  draft public.hof_seller_disclosure_drafts%rowtype;
begin
  if tg_op = 'UPDATE' then
    if row(new.draft_id, new.brokerage_id, new.agent_user_id, new.seller_email,
      new.seller_name, new.seller_index, new.token_hash, new.verification_code_hash,
      new.review_content_revision, new.review_render_revision)
      is distinct from row(old.draft_id, old.brokerage_id, old.agent_user_id, old.seller_email,
      old.seller_name, old.seller_index, old.token_hash, old.verification_code_hash,
      old.review_content_revision, old.review_render_revision) then
      raise exception using errcode = '55000', message = 'A review request cannot be reassigned to different answers or parties.';
    end if;
    if old.seller_attested_at is not null and row(new.seller_attested_at, new.seller_attested_name)
      is distinct from row(old.seller_attested_at, old.seller_attested_name) then
      raise exception using errcode = '55000', message = 'Completed seller reviews are retained unchanged.';
    end if;
    if old.revoked_at is not null and new.revoked_at is distinct from old.revoked_at then
      raise exception using errcode = '55000', message = 'A retired review request cannot be reactivated.';
    end if;
  end if;
  -- Serialize new links and completion with edits of the parent draft. Saving
  -- content never takes link locks, avoiding a parent/link lock inversion.
  if tg_op = 'INSERT' or (old.seller_attested_at is null and new.seller_attested_at is not null) then
    select * into draft from public.hof_seller_disclosure_drafts where id = new.draft_id for update;
    if not found or draft.status <> 'draft' or draft.signwell_document_id is not null
      or new.revoked_at is not null or new.review_content_revision is null
      or new.review_content_revision <> draft.review_content_revision
      or new.review_render_revision is null or length(new.review_render_revision) not between 1 and 200
      or new.brokerage_id <> draft.brokerage_id or new.agent_user_id <> draft.agent_user_id
      or new.seller_index is null or new.seller_index < 1
      or new.seller_index > jsonb_array_length(draft.seller_names)
      or lower(regexp_replace(btrim(coalesce(new.seller_name, '')), '\s+', ' ', 'g')) <>
        lower(regexp_replace(btrim(draft.seller_names ->> (new.seller_index - 1)), '\s+', ' ', 'g')) then
      raise exception using errcode = '55000', message = 'This disclosure changed. Ask the agent for an updated review request.';
    end if;
    if new.seller_attested_at is not null and lower(regexp_replace(btrim(coalesce(new.seller_attested_name, '')), '\s+', ' ', 'g')) <>
      lower(regexp_replace(btrim(new.seller_name), '\s+', ' ', 'g')) then
      raise exception using errcode = '55000', message = 'The seller name must match this review request.';
    end if;
  end if;
  return new;
end;
$$;

revoke all on function public.hof_guard_disclosure_review_content() from public, anon, authenticated;
revoke all on function public.hof_guard_disclosure_review_link() from public, anon, authenticated;
grant execute on function public.hof_guard_disclosure_review_content() to service_role;
grant execute on function public.hof_guard_disclosure_review_link() to service_role;
create trigger hof_disclosure_review_content_guard before insert or update on public.hof_seller_disclosure_drafts
  for each row execute function public.hof_guard_disclosure_review_content();
create trigger hof_disclosure_review_link_guard before insert or update on public.hof_seller_disclosure_review_links
  for each row execute function public.hof_guard_disclosure_review_link();

commit;
