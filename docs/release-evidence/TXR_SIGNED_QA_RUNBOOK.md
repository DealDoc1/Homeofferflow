# Restricted TXR signed-PDF QA runbook

This runbook is required before enabling production signing for TXR-1501,
TXR-1506, TXR-1507, or TXR-1508.

## Preconditions

- The brokerage source is approved in the private source vault.
- The brokerage authorization attestation and point-of-use agent attestation
  are present.
- `HOF_TXR_SIGNING_ENABLED=true` is set only in the isolated QA environment.
- SignWell remains in test mode for this run.
- No production user is sent a restricted form during QA.

## Per-form test

1. Create a private draft with the authenticated brokerage-member account.
2. Open the private unsigned preview and confirm every mapped field and
   checkbox against the approved source PDF.
3. Send the draft to the intended test recipients using distinct email
   addresses for each client.
4. Complete every required signer action in SignWell, including the associate
   or broker signer required by the selected signer plan.
5. Download the completed PDF from SignWell.
6. Render every page at 150 DPI and inspect every visible blank, checkbox,
   signature, and date line. Do not rely on extracted text alone.
7. Record the form code, source revision, SignWell document ID, signer plan,
   recipient roles, page count, and visual result in the release evidence file.

## Required evidence set

The release evidence must include one completed signed PDF review for each:

- TXR-1501
- TXR-1506
- TXR-1507
- TXR-1508

If any field, checkbox, recipient role, signature, or date is misplaced, keep
`HOF_TXR_SIGNING_ENABLED=false`, fix only the proven mapping, and repeat the
full affected-form review.

## Activation gate

Only after all four signed-PDF reviews pass may the restricted signing flag be
enabled in production. The final production deployment must include the
completed evidence file and a fresh full regression run.
