begin;

create table if not exists public.hof_offer_signing_parties (
  id uuid primary key default gen_random_uuid(),
  offer_id uuid not null references public.hof_offers(id) on delete cascade,
  created_by_user_id uuid not null references auth.users(id) on delete cascade,
  party_side text not null check (party_side in ('buyer', 'seller')),
  party_index smallint not null check (party_index between 1 and 4),
  full_name text not null check (length(trim(full_name)) between 1 and 250),
  email text,
  phone text,
  mailing_address text,
  signing_role text not null default 'party'
    check (signing_role in ('party', 'buyer', 'seller', 'landlord', 'tenant')),
  signing_required boolean not null default false,
  execution_status text not null default 'draft'
    check (execution_status in ('draft', 'pending', 'signed', 'declined', 'voided')),
  signwell_recipient_id text,
  signed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint hof_offer_signing_parties_offer_side_index_key
    unique (offer_id, party_side, party_index)
);

create index if not exists hof_offer_signing_parties_owner_offer_idx
  on public.hof_offer_signing_parties (created_by_user_id, offer_id);

create index if not exists hof_offer_signing_parties_offer_side_idx
  on public.hof_offer_signing_parties (offer_id, party_side, party_index);

alter table public.hof_offer_signing_parties enable row level security;

drop policy if exists hof_offer_signing_parties_owner_select on public.hof_offer_signing_parties;
create policy hof_offer_signing_parties_owner_select
  on public.hof_offer_signing_parties for select to authenticated
  using (
    created_by_user_id = (select auth.uid())
    and exists (
      select 1 from public.hof_offers o
      where o.id = hof_offer_signing_parties.offer_id
        and o.user_id = (select auth.uid())
    )
  );

drop policy if exists hof_offer_signing_parties_owner_insert on public.hof_offer_signing_parties;
create policy hof_offer_signing_parties_owner_insert
  on public.hof_offer_signing_parties for insert to authenticated
  with check (
    created_by_user_id = (select auth.uid())
    and exists (
      select 1 from public.hof_offers o
      where o.id = hof_offer_signing_parties.offer_id
        and o.user_id = (select auth.uid())
    )
  );

drop policy if exists hof_offer_signing_parties_owner_update on public.hof_offer_signing_parties;
create policy hof_offer_signing_parties_owner_update
  on public.hof_offer_signing_parties for update to authenticated
  using (
    created_by_user_id = (select auth.uid())
    and exists (
      select 1 from public.hof_offers o
      where o.id = hof_offer_signing_parties.offer_id
        and o.user_id = (select auth.uid())
    )
  )
  with check (
    created_by_user_id = (select auth.uid())
    and exists (
      select 1 from public.hof_offers o
      where o.id = hof_offer_signing_parties.offer_id
        and o.user_id = (select auth.uid())
    )
  );

drop policy if exists hof_offer_signing_parties_owner_delete on public.hof_offer_signing_parties;
create policy hof_offer_signing_parties_owner_delete
  on public.hof_offer_signing_parties for delete to authenticated
  using (
    created_by_user_id = (select auth.uid())
    and exists (
      select 1 from public.hof_offers o
      where o.id = hof_offer_signing_parties.offer_id
        and o.user_id = (select auth.uid())
    )
  );

revoke all on public.hof_offer_signing_parties from anon;
grant select, insert, update, delete on public.hof_offer_signing_parties to authenticated;

commit;

