# TXR-1507 Short Buyer/Tenant Representation Agreement — Implementation Plan

## Source reviewed

- **Form:** TXR-1507 Residential Buyer/Tenant Representation Agreement - Short Form
- **Revision:** 06-15-26
- **Length:** 2 pages
- **Source rule on the form:** Texas REALTORS member use only

The source is intentionally **not** included in the public repository. Each
agent using this workflow must affirm that they are currently authorized to use
the selected Texas REALTORS® form for their brokerage. The exact revision is
kept in the private, brokerage-scoped form-source vault before any signing
workflow is enabled. This is a source-control and correct-broker-identity
requirement; it is not an OnDemand-only approval requirement and does not
require Tyler Demando's approval for HomeOfferFlow product development.

## Agent intake

The agent must deliberately choose **Short Form** before any agreement data is
collected. HomeOfferFlow must not default a buyer into this agreement, choose
the Long Form, or infer compensation terms.

| Form paragraph | Agent-provided data | Required behavior |
|---|---|---|
| 1 Parties | One or more client names; broker legal name | Broker name comes from the approved brokerage profile, not a browser field. |
| 3 Market Area | Explicit geographic/property description | Required; block generation when blank. |
| 4 Term | Start date and end date | End date must be clear; display the form's 11:59 p.m. language. |
| 5 Services | `full_services` or `showing_services` | Mutually exclusive; showing-services path requires its execution fee. |
| 5 Showing fee | Dollar amount | Required only for `showing_services`. |
| 7A Purchase fee | Percentage and/or flat fee | Agent selects which approved fee fields apply; do not synthesize a fee. |
| 7A Lease fee | One-month-rent percentage, total-rents percentage, and/or flat fee | Agent selects only terms broker approves. |
| 8 Intermediary | Client authorizes / does not authorize | Required explicit choice. |

Draft validation requires an explicit service choice, valid ordered term dates,
and at least one agent-confirmed authorized purchase or lease compensation
field. It only
validates agent-entered values; it does not calculate or recommend compensation.

## Roles and signing

| Role | Responsibility | Signing fields |
|---|---|---|
| Brokerage / broker | Broker entity named in Paragraph 1 | Broker printed name, license, signature/date if broker elects to sign |
| Associate | Agent associated with the brokerage | Associate printed name/license and signature if applicable |
| Client 1 | Buyer or tenant client | Initial on page 1; signature/date on page 2 |
| Client 2 | Optional second buyer or tenant client | Initial on page 1; second signature/date on page 2 |

The signing plan must be confirmed against the authorized source before
activation. The current buyer-offer packet SignWell coordinates must never be
reused for this standalone agreement.

## Data and authorization safeguards

1. Require an active agent membership in the same brokerage as the approved
   TXR-1507 source and an explicit per-draft attestation that the agent is
   currently authorized to use that TXR form for the brokerage.
2. Require an approved form source for **TXR-1507** and its displayed revision.
3. Persist the source record ID, source revision, brokerage ID, agent ID, and
   final agreement record together.
4. Do not reveal the PDF source through browser Storage downloads.
5. Require explicit client review before SignWell submission.
6. Keep this workflow separate from the purchase-offer wizard and its
   Paragraph 22 addenda.

## Release QA

Before staging release, produce at least these completed packets and visually
inspect every printed blank, checkbox, initial, signature, and date:

| Scenario | Coverage |
|---|---|
| One buyer, full services, purchase percentage | Base purchase path |
| Two buyers, full services, purchase flat fee | Second client initials/signature |
| One tenant, showing services | Showing-services checkbox and required fee |
| Buyer/tenant with lease compensation | Each supported lease compensation field |
| Intermediary authorized | Paragraph 8 first checkbox |
| Intermediary not authorized | Paragraph 8 second checkbox |
| Missing market area / missing intermediary answer | Validation fails before any PDF/signing call |

## Production gate

The workflow remains unavailable until all of the following are complete:

1. An authorized source-owner administrator uploads and attests to the exact
   source revision in the private source vault.
2. The standalone agreement record/API and intake UI are implemented.
3. Completed SignWell staging packets pass the QA table above.
4. HomeOfferFlow release authority approves the rendered workflow, signing
   plan, and launch copy.

## Current implementation status

- The brokerage setup flow records whether the brokerage administrator attests
  that its agents are authorized to use Texas REALTORS® forms. This is a
  brokerage-level signal only; it does not replace each agent's own attestation.
- The TXR-1507 draft intake requires the individual agent to affirm current
  authorization and to select an approved private source revision.
- `api/txr_1507_renderer.py` now provides a source-bytes-in, two-page draft
  renderer with validation and a provisional coordinate map. It intentionally
  does not fetch or expose source PDFs, create SignWell packets, or imply that
  a draft is ready to sign.
- The renderer has been tested against a generated two-page fixture and one
  private rendering of the authorized TXR-1507 source. The private rendering
  still requires the scenario-by-scenario visual QA table above before any
  endpoint or signing release is enabled.
