# TXR-1508 Unrepresented Customer Showing Form

## Current released workflow

The February 25, 2026 workflow is production-live in the shared agent library.
Agents do not need a brokerage seat or a new source-owner approval to use the
released form. Its licensed source remains private and is already published.

The current one-customer completed-provider specimen was reviewed October 10.
The two-customer unsigned preview was also reviewed; that is not a completed
signing pass. A compact remaining test now covers the broker case, associate
case with different representation answers, and long/Unicode continuation:
four pages and 21 fields, all four unsigned pages visually reviewed.

This explicitly fictional test uses the two approved inboxes: professional
and customer 1 fields share QA A, and customer 2 uses QA B. Production roles
and geometry remain unchanged. Its protected control reserves one attempt,
forces nonbinding test mode and parallel invitations, disables reminders and
added signature pages, and never retrieves a new API key. Provider creation,
completion and final PDF review must be evidenced separately.

The draft-foundation notes below are historical, not current access rules.
Their source-owner and release-approval gates are superseded by the released
shared-library workflow; do not report them as new user blockers.

## Historical draft-foundation scope

This release creates a private, source-gated **draft intake** for the Texas
REALTORS(R) Unrepresented Customer Showing Form (TXR-1508, revision 02-25-26
reviewed locally). It now has a private-preview renderer and explicit signer
map in `api/txr_1508.py`, but it does not place live initials or signatures,
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
| Acknowledgement signer | Explicitly choose broker or associate with customers | Required; HomeOfferFlow never infers the responsible signer. |
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

The authorized one-page source was visually inspected and a sample overlay was
rendered for property, broker, associate, customer, and representation-status
fields. That is preview QA only; completed-signature visual QA is still
required before any send action is exposed.

Until those gates pass, the workflow remains a private draft record only.
