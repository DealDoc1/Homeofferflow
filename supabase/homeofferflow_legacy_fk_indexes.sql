-- Targeted foreign-key indexes from the production performance advisor.
-- These support relationship checks and cascading operations without changing
-- RLS, grants, data, or application behavior.

begin;

create index if not exists audit_log_offer_id_idx on public.audit_log (offer_id);
create index if not exists audit_log_transaction_id_idx on public.audit_log (transaction_id);
create index if not exists documents_offer_id_idx on public.documents (offer_id);
create index if not exists help_requests_offer_id_idx on public.help_requests (offer_id);
create index if not exists help_requests_transaction_id_idx on public.help_requests (transaction_id);
create index if not exists hof_partner_placements_brokerage_id_idx on public.hof_partner_placements (brokerage_id);
create index if not exists offer_invites_offer_id_idx on public.offer_invites (offer_id);
create index if not exists parties_transaction_id_idx on public.parties (transaction_id);
create index if not exists payments_offer_id_idx on public.payments (offer_id);
create index if not exists payments_transaction_id_idx on public.payments (transaction_id);
create index if not exists sign_requests_offer_id_idx on public.sign_requests (offer_id);

commit;
