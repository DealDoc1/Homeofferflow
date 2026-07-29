-- HomeOfferFlow legacy-table Data API hardening
--
-- These original tables are not used by the current application. They already
-- have RLS enabled with no browser policies, but broad default table grants
-- still made their names discoverable through the Data API / GraphQL schema.
-- Keep service_role access for operational recovery while removing every
-- browser-side privilege.

begin;

revoke all on table
  public.audit_log,
  public.documents,
  public.help_requests,
  public.offer_intakes,
  public.offer_invites,
  public.offer_terms,
  public.offers,
  public.parties,
  public.payments,
  public.sign_requests,
  public.transactions
from anon, authenticated;

commit;
