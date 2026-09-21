# FSBO seller guided validation — 2026-09-21

## Scope

- Keep both FSBO seller-plan actions usable before the required address and
  email are complete.
- Preserve the existing Google address autocomplete and manual-entry fallback.
- Preserve the existing validation, duplicate protection, private browser
  draft, server save, seller-plan receipt, and optional paid-path behavior.
- On an incomplete attempt, focus the missing address or email and explain the
  exact correction instead of leaving the seller with a disabled action.

## Verification

- Focused FSBO suite: 71 tests passed.
- Local browser QA at `/?seller=1`:
  - The initial action was enabled and labeled with `0 of 2` progress.
  - Entering an address changed the action to `1 of 2` progress.
  - Selecting the action at `1 of 2` focused the missing Email field.
  - A valid address and email restored `Get My Free Seller Plan`.
  - Google autocomplete help and manual-address guidance remained visible.
  - No seller request was submitted during QA.
- Visual review confirmed the existing compact two-field layout remains intact
  without an added panel or extra required question.

## Release state

Implemented and locally verified. Include in the next intentional bundled
production release after the Vercel capacity check.
