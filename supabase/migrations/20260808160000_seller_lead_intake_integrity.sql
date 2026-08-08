-- Seller-lead intake integrity hardening.
--
-- The public FSBO lead endpoint intentionally writes through the service role,
-- while signed-in agents use the authenticated browser path.  Keep those two
-- paths separate and constrain the values stored by either path.

begin;

update public.hof_seller_leads
set seller_type = 'fsbo'
where seller_type is null;

update public.hof_seller_leads
set status = 'new'
where status is null;

alter table public.hof_seller_leads
  alter column seller_type set default 'fsbo',
  alter column seller_type set not null,
  alter column property_address set not null,
  alter column status set default 'new',
  alter column status set not null;

alter table public.hof_seller_leads
  drop constraint if exists hof_seller_leads_seller_type_allowed,
  drop constraint if exists hof_seller_leads_status_allowed,
  drop constraint if exists hof_seller_leads_property_address_length,
  drop constraint if exists hof_seller_leads_seller_name_length,
  drop constraint if exists hof_seller_leads_seller_email_length,
  drop constraint if exists hof_seller_leads_seller_phone_length,
  drop constraint if exists hof_seller_leads_notes_length,
  drop constraint if exists hof_seller_leads_amounts_nonnegative;

alter table public.hof_seller_leads
  add constraint hof_seller_leads_seller_type_allowed
    check (seller_type in ('agent_listing', 'fsbo')),
  add constraint hof_seller_leads_status_allowed
    check (status in ('new', 'contacted', 'qualified', 'converted', 'archived')),
  add constraint hof_seller_leads_property_address_length
    check (length(btrim(property_address)) between 3 and 500),
  add constraint hof_seller_leads_seller_name_length
    check (seller_name is null or length(btrim(seller_name)) between 1 and 250),
  add constraint hof_seller_leads_seller_email_length
    check (seller_email is null or length(btrim(seller_email)) between 3 and 254),
  add constraint hof_seller_leads_seller_phone_length
    check (seller_phone is null or length(btrim(seller_phone)) between 3 and 80),
  add constraint hof_seller_leads_notes_length
    check (notes is null or length(notes) <= 1500),
  add constraint hof_seller_leads_amounts_nonnegative
    check (
      (asking_price is null or asking_price >= 0)
      and (mortgage_balance is null or mortgage_balance >= 0)
    );

create or replace function public.hof_touch_seller_lead_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists hof_seller_leads_touch_updated_at
  on public.hof_seller_leads;

create trigger hof_seller_leads_touch_updated_at
before update on public.hof_seller_leads
for each row execute function public.hof_touch_seller_lead_updated_at();

drop policy if exists hof_seller_leads_insert_own on public.hof_seller_leads;
create policy hof_seller_leads_insert_own
  on public.hof_seller_leads for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists hof_seller_leads_select_own on public.hof_seller_leads;
create policy hof_seller_leads_select_own
  on public.hof_seller_leads for select
  to authenticated
  using ((select auth.uid()) = user_id);

revoke all on function public.hof_touch_seller_lead_updated_at() from public;

commit;
