# Brokerage admin and TXR gate live-state evidence

## Scope

This is a read-only live-state check for the OnDemand Realty brokerage. It
does not change brokerage authorization, upload a source form, invite an
agent, or activate a legal-form workflow.

## Verified live state

- Brokerage: OnDemand Realty (`ondemand`)
- Brokerage administrator record: Tyler Demando is represented as the active
  brokerage administrator.
- Brokerage-wide Texas REALTORS® / NAR authorization: **not attested**.
- Private brokerage TXR source rows: **0**.
- Approved and attested TXR source rows: **0**.
- Restricted TXR workflows therefore remain locked by design.

## Product behavior verified

- The public OnDemand launch page displays the 60-day trial, $29/month renewal,
  current purchase-offer scope, and the limitation that standalone
  representation/listing/seller-disclosure workflows are not yet live.
- The brokerage setup includes an explicit NAR/Texas REALTORS® authorization
  question and administrator attestation.
- Each agent must separately attest at point of use.
- Source approval, draft creation, sending, signing, and release authority
  remain separate gates.
- Brokerage activity visibility remains aggregate-only; buyer names, property
  addresses, offer terms, and document contents are not exposed in the broker
  summary contract.

## Not completed in this check

Authenticated interactive brokerage-admin QA was not completed because the
available app tab was not signed into the HomeOfferFlow workspace. No attempt
was made to send a magic link, change the authorization state, or upload a
private source PDF.

## Required next evidence

1. Sign in as an active brokerage administrator in the production workspace.
2. Verify authorization, branding, shared defaults, roster, and invitation
   controls using `docs/BROKERAGE_ADMIN_LIVE_QA.md`.
3. If the source-owner workflow is intentionally activated, upload the exact
   approved source PDF, record its fingerprint, and complete signer-plan,
   rendered-PDF, and completed-signature QA before any release decision.
