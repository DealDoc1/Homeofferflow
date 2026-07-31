# Brokerage Admin Live QA

This checklist verifies the production brokerage workspace without exposing
buyer names, property addresses, offer terms, or document contents.

## Preconditions

- Sign in as an active `brokerage_admin` for the brokerage being tested.
- Use the canonical production site, not a preview deployment.
- Do not upload a source form or mark a TXR source approved during ordinary QA.
- Do not send a real invitation unless the broker has supplied the agent email
  and the invitation is intentionally part of the test.

## OnDemand broker-admin scenario

1. Open the Agent / Broker workspace and open the Brokerage tab.
2. Confirm the brokerage name and the broker-admin role are displayed.
3. Confirm the activity panel shows only operational totals and does not show
   buyer names, property addresses, offer terms, or document contents.
4. Confirm the TXR / NAR authorization control is visible to the broker admin.
5. Confirm the control explains that each agent must attest individually and
   that an approved private source is required separately.
6. Leave the status as `Not confirmed yet` unless the broker is intentionally
   recording the brokerage assertion. A brokerage assertion must never be
   inferred from a license number or silently written by an agent.
7. Verify branding controls reject invalid colors and reject non-image files or
   files larger than 2 MB. If a logo is intentionally uploaded, verify it is
   visible only as brokerage branding.
8. Verify shared title defaults can be saved and that an agent must explicitly
   copy them into their own profile; saving defaults must not alter an existing
   offer.
9. If an invitation is intentionally tested, verify it is email-bound, expires
   in 14 days, grants agent access only, and does not cancel or change the
   invitee's HomeOfferFlow subscription.
10. As the invited agent, accept the invitation with the matching email and
    verify the membership is active. Confirm the agent cannot see brokerage
    activity totals for other members or change brokerage authorization.

## TXR/NAR authorization behavior

- The brokerage administrator may record whether participating agents are
  authorized Texas REALTORS® / NAR members or otherwise authorized by the
  source owner.
- Every agent must still attest to their own current authorization before
  creating a restricted TXR draft.
- The exact private source PDF must be uploaded and attested by an authorized
  source owner before the form is exposed.
- HomeOfferFlow release authority and completed rendered/signature QA remain
  separate release gates.

## Evidence to record

Record the date, production URL, signed-in role, visible controls, and result of
each step. Do not record buyer-sensitive values. Mark the roadmap item partial
until this checklist has been completed in a signed-in production session.
