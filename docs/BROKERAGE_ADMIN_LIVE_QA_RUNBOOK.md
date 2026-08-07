# Brokerage-admin live QA runbook

Use this runbook with an authenticated active `brokerage_admin` account. It is
an observation checklist, not an authorization to activate restricted Texas
REALTORS® forms.

## Automated preflight (run this first)

Before opening the interactive checklist, run the read-only verifier with an
existing Supabase access token:

```bash
HOF_ACCESS_TOKEN='YOUR_TOKEN' python scripts/verify_brokerage_admin_live.py \
  --base-url https://www.homeofferflow.com \
  --brokerage-slug ondemand
```

The verifier calls only `GET /api/admin-dashboard?scope=brokerage`. It does
not create invites, change membership, update branding, read offer terms, or
send documents. It writes a metadata-only report and fails if aggregate
metrics, roster/source-readiness metadata, or the privacy contract are
missing. Do not paste the token or the report into a public issue.

Expected result:

```json
{ "ok": true, "brokerage": { "slug": "ondemand" }, "errors": [] }
```

A failed preflight is a stop condition: fix the API/authorization/privacy
problem before performing the interactive steps below.

## Preconditions

- Open `https://www.homeofferflow.com/` in a clean browser session.
- Sign in as the brokerage administrator for the brokerage being tested.
- Use a test agent email controlled by the reviewer. Do not use a client email
  or real transaction information.
- Record the production commit and date before starting the run.

## QA sequence

### 1. Brokerage identity and role

- Open Account → Brokerage.
- Confirm the correct brokerage name is displayed.
- Confirm the account is identified as a brokerage administrator.
- Confirm ordinary agent controls are not presented as broker controls.

Expected: the administrator sees the brokerage workspace; an agent’s personal
offer workflow remains available; no buyer or seller transaction data is shown
in the brokerage summary.

### 2. Privacy-limited dashboard

- Review the roster and aggregate activity cards.
- Confirm the dashboard shows only operational totals, membership state,
  subscription state, and agent-level activity counts.
- Confirm it does not show buyer names, buyer emails, property addresses,
  offer prices, offer terms, document contents, or signing-document contents.

Expected: privacy boundaries remain intact in both the rendered UI and the
network response used to populate the brokerage summary.

### 3. Branding and shared defaults

- Save a harmless test brand color.
- If desired, upload a brokerage-owned PNG/JPG/WebP logo no larger than 2 MB.
- Save a test title-company and escrow-contact suggestion.
- Sign out or reload, then confirm the saved values reload.
- In an agent account connected to the brokerage, confirm the agent must
  explicitly choose whether to copy title defaults into the agent profile.

Expected: only the active brokerage administrator can change branding/defaults;
agent opt-in does not modify an existing offer.

### 4. Invitation creation

- Enter the controlled test agent email and create one invite link.
- Confirm the result says the link is email-bound and expires in 14 days.
- Confirm the dashboard does not display the raw invite token after creation.
- Confirm a second pending invite for the same email reuses or refreshes the
  existing pending invite rather than creating an unbounded set.

Expected: the invite is agent-only, brokerage-scoped, and does not start agent
billing until the invited user completes the normal Stripe checkout.

### 5. Invitation acceptance

- Open the invite in a separate test-agent session using the invited email.
- Create/sign in to the agent account and accept the invite.
- Confirm the profile connects to the intended brokerage and membership becomes
  active with role `agent`.
- Attempt the same invite with a different email.

Expected: the invited email succeeds; a different email is rejected before any
profile or membership write; the invite cannot be accepted twice.

### 6. Membership control

- As the brokerage administrator, suspend the test agent.
- Confirm the agent loses brokerage-managed access only.
- Confirm the UI does not offer controls to cancel the agent’s HomeOfferFlow
  subscription, delete the agent’s offers, or change the agent’s account role.
- Restore the agent and confirm active access returns.

Expected: broker controls are limited to the brokerage membership record.

### 7. Packet and signing-message propagation

- Have the connected test agent create a harmless test offer using non-client
  data.
- Confirm the brokerage identity appears only where the product promises it:
  packet/signing-message brokerage context and the agent’s connected workspace.
- Confirm buyer-sensitive fields remain unavailable to the brokerage summary.

Expected: propagation is visible and accurate, while privacy-limited brokerage
views remain free of buyer/property/offer details.

### 8. Restricted-form negative gate

- Leave brokerage Texas REALTORS® / NAR authorization at “Not confirmed yet.”
- Confirm restricted-form readiness remains locked.
- Confirm no source PDF, source URL, fingerprint, or document contents are
  exposed in the ordinary brokerage dashboard.
- Do not upload a source or activate a restricted workflow during this run.

Expected: no restricted form can be drafted, sent, or signed from this QA run.

## Evidence to record

Record only:

- production commit and date;
- verifier result and timestamp;
- reviewer role (brokerage administrator);
- brokerage slug/name;
- pass/fail for each numbered section;
- redacted screenshots where useful;
- error text and timestamp for any failure.

Do not record client names, exact addresses, MLS numbers, phone numbers, email
addresses, offer terms, document contents, invite tokens, or source PDF hashes.

## Release decision

Mark the brokerage workspace passed only after all sections pass in an
authenticated session. A pass here does not authorize restricted legal-form
generation or signing; those workflows still require an approved private source,
document-specific signer plan, rendered-PDF QA, completed-signature visual QA,
and product release authority.
