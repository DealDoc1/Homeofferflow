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

## Exact OnDemand/Texas REALTORS® gate run

Use this sequence for the first authenticated broker-admin session. It is
intentionally separate from ordinary branding and roster QA:

1. Leave the brokerage status at `Not confirmed yet` and verify every
   restricted TXR workflow remains locked.
2. Select `Yes — all participating agents are authorized Texas REALTORS® / NAR
   users`, check the administrator attestation, and save.
3. Verify the success message still says that each agent must attest
   individually and that an approved private source is required separately.
4. Sign in as an agent in the same brokerage. Verify the agent can see the
   restricted-form card but cannot start a draft until an approved private
   source exists and the agent checks the individual membership/authority
   attestation.
5. If a source-owner upload is intentionally part of the test, upload only the
   authorized private PDF, confirm its SHA-256 fingerprint, attest to that
   exact source, and verify the source remains private and brokerage-scoped.
   Source approval alone must not create, send, or sign a document.
6. Re-test the negative path by changing the brokerage status to `No / not all
   participating agents are authorized`; verify restricted workflows lock
   again and an agent cannot override that state.
7. Do not mark a TXR workflow released until its completed signed PDF has been
   visually inspected page-by-page and release authority has recorded approval.

Expected evidence for the first OnDemand session:

| Check | Expected result |
|---|---|
| Broker account | Tyler Demando, `brokerage_admin`, active OnDemand membership |
| Brokerage assertion | Saved only by the broker-admin, with actor and timestamp |
| Agent assertion | Required at point of use; never inferred from a license number |
| Source PDF | Private, exact fingerprint recorded, no browser download for agents |
| Draft behavior | Private draft only until separate rendered/signing release |
| Negative path | `No / not all` locks restricted workflows again |

## Evidence to record

Record the date, production URL, signed-in role, visible controls, and result of
each step. Do not record buyer-sensitive values. Mark the roadmap item partial
until this checklist has been completed in a signed-in production session.
