# HomeOfferFlow — Agent Form Coverage Roadmap

## Launch scope: OnDemand Realty

The OnDemand launch is intentionally scoped to the current **buyer-side offer
packet** and its currently supported purchase addenda. It is not represented as
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
- Agent accounts, OnDemand attribution, a 60-day card-required trial, and
  broker-level aggregate activity visibility with buyer and property details
  withheld.

## Priority release order

### 1. Buyer representation agreement

This is the first missing agent workflow because it belongs at the beginning of
the buyer relationship, before an offer is prepared.

Important source-form rule: TREC does **not** promulgate a buyer representation
agreement. OnDemand must provide the broker-approved agreement and confirm the
right to use it in HomeOfferFlow before implementation. The product must not
substitute, generate, or improvise legal agreement language.

Release requirements:

- broker-approved source PDF/template and version owner;
- guided data intake limited to the approved agreement fields;
- correct agent, broker, and buyer signer/recipient roles;
- secure association to the agent and brokerage;
- rendered-PDF, signature-placement, and single-/multi-buyer QA;
- broker approval before production release.

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
- broker approval before production release.

### 3. Listing agreement workflow

Build this as the opening of the seller/listing workspace, paired with the
seller disclosure workflow rather than as another offer addendum. Listing
agreements are brokerage/private agreements, so OnDemand must supply the
broker-approved source agreement and authorize its use before implementation.

Release requirements:

- broker-approved source agreement and version owner;
- seller, listing agent, broker, and any team/supervisor roles defined by
  OnDemand;
- listing-specific data intake and electronic signatures;
- visibility limited to the assigned brokerage team and authorized broker
  administrators;
- rendered-PDF, signature-placement, and multi-seller QA;
- broker approval before production release.

### 4. Core transaction follow-up forms

After the relationship and listing foundations are live, add the documents
agents most often need after an offer is written: approved amendments,
termination/notice workflows, and remaining broker-approved transaction forms.
Each form is a separate release, not a checkbox added to the offer wizard.

## Non-negotiable release gate for every new form

1. **Approved source:** confirm the official or brokerage-approved source form,
   current version, and authority to use it.
2. **Data model:** add only the information needed for that document and keep
   buyer/seller data separated by role.
3. **Signing plan:** define each recipient, signing order, and broker oversight
   before any e-signature fields are placed.
4. **Visual QA:** inspect every applicable blank, checkbox, initial, signature,
   and date on a rendered completed PDF.
5. **Regression:** add a dedicated golden test packet for the new form and run
   existing purchase-packet regressions.
6. **Broker approval:** Tyler Demando or his delegated OnDemand reviewer signs
   off on the source form, workflow, and release copy before production.

## Communication rule

Until each workflow passes the release gate, sales, onboarding, and the product
UI must say **"currently supported buyer-side offer packets and addenda"** —
not "all agent forms," "complete transaction management," or equivalent broad
claims.
