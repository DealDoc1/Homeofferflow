# TXR-1501 Long Buyer/Tenant Representation Agreement - Draft Foundation

## Scope of this release

This release creates only a private, source-gated **draft intake** for the
Texas REALTORS(R) Residential Buyer/Tenant Representation Agreement - Long
Form (TXR-1501, revision 06-15-26 reviewed locally). It does not create a PDF,
place signatures, send an agreement, or expose a member source PDF.

The agent must deliberately choose the Long Form. HomeOfferFlow must never
select it for a client or substitute it for TXR-1507 Short Form.

## Draft intake

The Long Form intake records the following agent-entered terms privately:

| Form area | Intake data | Guardrail |
| --- | --- | --- |
| Parties | One or two client names and client contact details | The final broker details must come from the brokerage profile, not a browser field. |
| Market Area / Term | Market area and ordered start/end dates | Never permit a blank market area or an end date before the start date. |
| Broker compensation | Purchase and lease percentage and/or flat-fee terms | Require at least one broker-approved term; do not calculate or suggest a fee. |
| Retainer | Optional amount and treatment election | Require an explicit treatment only if a retainer is supplied. |
| Protection period | Optional whole-number days | Store only an agent-confirmed broker-approved value. |
| Payment county | County for payment direction | Required for the eventual mapping. |
| Intermediary | Authorized or not authorized | Require an explicit selection. |

## Signing and release gate

Before this becomes a completed or sent agreement, HomeOfferFlow must have:

1. A current TXR-1501 source privately uploaded and expressly approved by an
   authorized OnDemand brokerage administrator.
2. A form-specific field map for all six pages, including broker/associate
   information, client initials, and both client signature lines.
3. A broker-approved signer plan for broker, associate, and one- or two-client
   variants.
4. Rendered and completed SignWell QA for each applicable printed blank,
   checkbox, initial, signature, and date.
5. OnDemand approval of the final source revision and client-facing language.

Until those gates pass, the workflow remains a private draft record only.
