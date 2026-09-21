# Partner application guided validation — 2026-09-21

## Scope

- Keep the primary partner-application action operable before the five required
  details and terms acknowledgement are complete.
- Preserve the existing server submission and Stripe checkout gates.
- On an incomplete attempt, focus the first missing required field and explain
  the exact next action instead of leaving the visitor with a disabled button.
- Keep the existing draft recovery, tier pricing, consent language, privacy
  controls, and checkout behavior unchanged.

## Verification

- Focused partner suite: 71 tests passed.
- Full regression suite: 2,369 tests passed.
- Local browser QA at `/?partner=1&partner_quick_start=1`:
  - The initial action was enabled and labeled with `0 of 5` progress.
  - Selecting the initial action focused the missing Partner category field.
  - After all five essentials were entered, the action changed to
    `Review terms to continue`.
  - Selecting it focused the unchecked terms acknowledgement.
  - No application was saved and no checkout was opened during QA.
- Visual review confirmed the change uses the existing button and status areas
  without adding a new panel or additional page clutter.

## Release state

Implemented and locally verified. Include in the next intentional bundled
production release after the Vercel capacity check.
