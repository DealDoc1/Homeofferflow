# Buyer acknowledgement guidance — 2026-09-21

## Scope

- Keep the opening buyer-interview action usable before the required legal
  acknowledgement is checked.
- Preserve the acknowledgement as a mandatory gate; do not advance or record
  acceptance from an action-button click.
- Explain the missing action in plain language, mark and focus the checkbox,
  and clear the warning immediately after acknowledgement.
- Preserve every later interview validation, packet-generation, and payment
  safeguard.

## Verification

- Focused buyer-navigation and validation suite: 10 tests passed.
- Runtime coverage confirms an unacknowledged attempt does not collect answers,
  validate later fields, or advance the interview.
- Local browser QA at `/?buyer=1` confirmed:
  - The initial action reads `Acknowledge to continue` and is operable.
  - Selecting it displays a concise instruction and focuses the unchecked box.
  - Checking the box clears the warning and changes the action to `Continue`.
  - Selecting Continue advances to the property-visit question.
- No offer, customer information, checkout, or packet was submitted during QA.

## Release state

Implemented and locally verified. Include in the next intentional bundled
production release after the Vercel capacity check.
