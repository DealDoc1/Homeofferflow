# TXR-1508 Unrepresented Customer Showing Form - Draft Foundation

## Scope of this release

This release creates a private, source-gated **draft intake** for the Texas
REALTORS(R) Unrepresented Customer Showing Form (TXR-1508, revision 02-25-26
reviewed locally). It does not create a PDF, place initials or signatures,
send a showing form, or expose a member source PDF.

TXR-1508 is not a buyer representation agreement. HomeOfferFlow must never
use it to imply agency, compensation, advice, or any brokerage service beyond
the limited unrepresented-customer showing workflow described in the approved
source.

## Draft intake

| Form area | Intake data | Guardrail |
| --- | --- | --- |
| Property | Street address and city | Required; do not infer a property from a lead. |
| Customer | One or two customer names | Do not reuse a buyer-representation draft without an explicit agent choice. |
| Other representation | One explicit yes/no answer for each customer | A blank answer cannot be saved. |
| Limits acknowledgement | Agent confirms the unrepresented, no-compensation, and no-advice limits | Required before the private draft can be saved. |
| Broker information | Broker firm and associate fields | Final values must come from the brokerage profile, never a browser field. |

## Signing and release gate

Before this becomes a completed or sent showing form, HomeOfferFlow must have:

1. A current TXR-1508 source privately uploaded and attested by an authorized
   source-owner administrator.
2. A field map for every printed blank, checkbox, broker initial, customer
   initial, date, and one- or two-customer variant.
3. An authorized signer and initials plan.
4. Rendered and completed SignWell QA for every applicable printed field.
5. HomeOfferFlow release-authority approval of the final workflow and
   customer-facing copy.

Until those gates pass, the workflow remains a private draft record only.
