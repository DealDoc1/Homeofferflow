# HomeOfferFlow — Agent Form Coverage Roadmap

## Launch scope: OnDemand Realty

The OnDemand launch is intentionally scoped to the current **purchase-offer
packet** and its currently supported purchase addenda, including the Seller
Temporary Residential Lease when seller post-closing possession applies. It is not represented as
a complete transaction-form library or a transaction-management platform.

Agents must continue using OnDemand-approved workflows for standalone buyer
representation agreements, listing agreements, seller disclosure notices, and
any other documents not expressly available in HomeOfferFlow.

This language appears on `/ondemand` before an agent begins the 60-day trial.

## What is live now

- Guided buyer-side offer preparation.
- The current production purchase contract workflow and its supported purchase
  addenda.
- Buyer electronic-signature delivery for the generated offer packet.
- Seller Temporary Residential Lease (TREC 15-7) when the seller remains in
  possession after closing, including the defined buyer/landlord and
  seller/tenant execution roles.
- Agent accounts, OnDemand attribution, a 60-day card-required trial, and
  broker-level aggregate activity visibility with buyer and property details
  withheld.

## Priority release order

### 1. Buyer representation agreement

This is the first missing agent workflow because it belongs at the beginning of
the buyer relationship, before an offer is prepared.

Important source-form rule: TREC does **not** promulgate a buyer representation
agreement. For the Texas REALTORS® member workflow, the approved source forms
are TXR-1501 Residential Buyer/Tenant Representation Agreement - Long Form and
TXR-1507 Residential Buyer/Tenant Representation Agreement - Short Form. The
agent must choose the correct authorized form; HomeOfferFlow must not
silently default a client into either agreement or improvise legal agreement
language.

The supplied July 2026 Texas REALTORS® source-form inventory also identifies
TXR-1506 General Information and Notice to Consumers and TXR-1508
Unrepresented Customer Showing Form as closely related buyer-intake workflows.
They are separate releases, not addenda to a purchase offer.

Release requirements:

- authorized source PDF/template and version owner;
- an explicit per-agent attestation that the user is currently authorized to
  use the selected Texas REALTORS® form for the user's brokerage (the source
  form itself limits use to authorized members), plus a private source record
  for the exact revision;
- an explicit agent choice between the Long Form and Short Form, with no
  preselected legal agreement;
- guided data intake limited to the approved agreement fields;
- correct agent, broker, and buyer signer/recipient roles;
- secure association to the agent and brokerage;
- rendered-PDF, signature-placement, and single-/multi-buyer QA;
- HomeOfferFlow release authority approval before production release;
- source-owner attestation when a customer brokerage supplies a private source.

Foundation completed locally: `supabase/homeofferflow_brokerage_form_sources.sql`
creates a private brokerage-source vault for TXR-1501, TXR-1506, TXR-1507,
and TXR-1508. It requires a brokerage administrator's authorization attestation
and deliberately prevents agents from downloading restricted source PDFs in
their browsers. It does not activate or distribute a form by itself.

The source-specific renderer and signer-map foundation is now staged in
`api/txr_1507.py`. It preserves the supplied two-page source, overlays only
validated intake values, and keeps the client one- and client two-signer maps
separate from the purchase-packet coordinates. This is renderer QA work, not
an executable or production signing release: an authorized brokerage
administrator must still upload and attest to the source, and the associate /
client signing order must pass completed SignWell visual QA before a send
action is exposed.

### 2. Seller disclosure workflow

Build this as a seller-side workflow, separate from the buyer offer wizard.
It must collect seller responses, preserve the seller's review responsibility,
and route the completed disclosure to the correct recipients. It must not be
confused with the purchase contract's question about whether a disclosure has
already been received.

Release requirements:

- use the current approved disclosure form and version;
- seller-only questionnaire and electronic-signature workflow;
- property and listing association with access controls;
- visible review/attestation step for the seller;
- rendered-PDF and field-by-field QA;
- HomeOfferFlow release authority approval before production release.

### 3. Listing agreement workflow

Build this as the opening of the seller/listing workspace, paired with the
seller disclosure workflow rather than as another offer addendum. Listing
agreements are usually organization-private agreements, so the source owner
must supply the authorized source agreement and attest to its use before
implementation.

Release requirements:

- authorized source agreement and version owner;
- seller, listing agent, broker, and any team/supervisor roles defined by the
  source-owning organization;
- listing-specific data intake and electronic signatures;
- visibility limited to the assigned organization team and authorized
  administrators;
- rendered-PDF, signature-placement, and multi-seller QA;
- HomeOfferFlow release authority approval before production release.

### 4. Core transaction follow-up forms

After the relationship and listing foundations are live, add the documents
agents most often need after an offer is written: approved amendments,
termination/notice workflows, and remaining authorized transaction forms.
Each form is a separate release, not a checkbox added to the offer wizard.

## Non-negotiable release gate for every new form

1. **Approved source:** confirm the official or source-owner-authorized form,
   current version, and authority to use it.
2. **Data model:** add only the information needed for that document and keep
   buyer/seller data separated by role.
3. **Signing plan:** define each recipient, signing order, and applicable
   organization oversight before any e-signature fields are placed.
4. **Visual QA:** inspect every applicable blank, checkbox, initial, signature,
   and date on a rendered completed PDF.
5. **Regression:** add a dedicated golden test packet for the new form and run
   existing purchase-packet regressions.
6. **Release authority:** HomeOfferFlow's CEO or delegated product reviewer
   signs off on the workflow and release copy before production. If a customer
   brokerage or organization supplies a private source, its authorized source
   owner must separately attest to the source and version.

## Communication rule

Until each workflow passes the release gate, sales, onboarding, and the product
UI must say **"currently supported purchase-offer packets and addenda"** —
not "all agent forms," "complete transaction management," or equivalent broad
claims.
