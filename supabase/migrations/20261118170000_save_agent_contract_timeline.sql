begin;

create or replace function public.hof_save_agent_contract_timeline(
  p_offer_id uuid,
  p_owner_id uuid,
  p_expected_status text,
  p_expected_updated_at text,
  p_expected_option_days jsonb,
  p_tracking jsonb
)
returns jsonb
language sql
security invoker
set search_path = ''
as $$
  update public.hof_offers
     set offer_data = jsonb_set(coalesce(offer_data, '{}'::jsonb), '{transactionTracking}', p_tracking)
   where id = p_offer_id
     and user_id = p_owner_id
     and deleted_at is null
     and status is not distinct from p_expected_status
     and offer_data #>> '{transactionTracking,updatedAt}' is not distinct from p_expected_updated_at
     and coalesce(offer_data->'optionDays', offer_data->'option_days', to_jsonb(option_days), 'null'::jsonb)
         = coalesce(p_expected_option_days, 'null'::jsonb)
     and jsonb_typeof(coalesce(offer_data, '{}'::jsonb)) = 'object'
     and jsonb_typeof(p_tracking) = 'object'
  returning offer_data->'transactionTracking';
$$;

revoke all on function public.hof_save_agent_contract_timeline(uuid, uuid, text, text, jsonb, jsonb)
  from public, anon, authenticated;
grant execute on function public.hof_save_agent_contract_timeline(uuid, uuid, text, text, jsonb, jsonb)
  to service_role;

commit;
