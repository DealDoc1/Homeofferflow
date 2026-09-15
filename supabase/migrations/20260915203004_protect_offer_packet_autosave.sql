-- Browser draft editing must not change an existing packet or its delivery journal.
-- Service-role rendering, delivery checkpoints and webhooks retain their access.
create function public.hof_protect_offer_packet_autosave()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
declare
  private_keys text[] := array[
    '_hof_signature_delivery', '_subscription_user_id', '_paragraph4_source_pdf_bytes',
    'backend_saved', 'signwell', 'signwellDocumentId', 'signwellStatus',
    'signwell_document_id', 'signwell_status', 'generatedAt', 'generated_at',
    'packetGeneratedAt', 'packetGenerationError', 'packetGenerationFailedAt',
    'packetGenerationFailureCategory', 'signwellLastStatusRefresh', 'signwellRecipientStatuses',
    'signingUrl', 'signing_url', 'embeddedSigningUrl', 'embedded_signing_url', 'recipients'
  ];
  protected_packet boolean;
  preserved jsonb;
begin
  if current_user not in ('anon', 'authenticated') then
    return NEW;
  end if;
  if TG_OP = 'UPDATE' then
    if NEW.id is distinct from OLD.id or NEW.user_id is distinct from OLD.user_id then
      raise exception using errcode = '42501', message = 'Offer ownership cannot be changed.';
    end if;
    protected_packet := OLD.generated_at is not null
      or nullif(OLD.signwell_document_id, '') is not null
      or nullif(OLD.offer_data->>'generatedAt', '') is not null
      or nullif(OLD.offer_data->>'generated_at', '') is not null
      or nullif(OLD.offer_data->>'signwellDocumentId', '') is not null
      or nullif(OLD.offer_data->>'signwell_document_id', '') is not null
      or nullif(OLD.offer_data#>>'{signwell,document_id}', '') is not null
      or nullif(OLD.offer_data#>>'{signwell,response,id}', '') is not null
      or coalesce(OLD.offer_data, '{}'::jsonb) ? '_hof_signature_delivery'
      or lower(coalesce(OLD.status, 'draft')) not in ('draft', 'generation failed');
    if protected_packet then
      -- An explicit dashboard soft-delete is still allowed. No other answer,
      -- column, receipt, or state mutation can ride along with that operation.
      if (to_jsonb(NEW) - array['status','deleted_at','last_updated','updated_at'])
           is distinct from
         (to_jsonb(OLD) - array['status','deleted_at','last_updated','updated_at'])
         or not coalesce((NEW.status is not distinct from OLD.status
                 and NEW.deleted_at is not distinct from OLD.deleted_at
                 or NEW.status = 'Deleted' and NEW.deleted_at is not null), false) then
        raise exception using errcode = '55000',
          message = 'This packet is already prepared. Save changes as a new draft.';
      end if;
      return NEW;
    end if;
    NEW.signwell_document_id := OLD.signwell_document_id;
    NEW.signwell_status := OLD.signwell_status;
    NEW.generated_at := OLD.generated_at;
    if NEW.status is distinct from 'Deleted' or NEW.deleted_at is null then
      NEW.status := OLD.status;
    end if;
    select coalesce(jsonb_object_agg(key, value), '{}'::jsonb) into preserved
      from jsonb_each(coalesce(OLD.offer_data, '{}'::jsonb)) where key = any(private_keys);
    NEW.offer_data := (coalesce(NEW.offer_data, '{}'::jsonb) - private_keys) || preserved;
  else
    NEW.status := 'Draft';
    NEW.signwell_document_id := null;
    NEW.signwell_status := null;
    NEW.generated_at := null;
    NEW.offer_data := coalesce(NEW.offer_data, '{}'::jsonb) - private_keys;
  end if;
  return NEW;
end;
$$;

revoke all on function public.hof_protect_offer_packet_autosave() from public, anon, authenticated;
create trigger hof_protect_offer_packet_autosave
before insert or update on public.hof_offers
for each row execute function public.hof_protect_offer_packet_autosave();
