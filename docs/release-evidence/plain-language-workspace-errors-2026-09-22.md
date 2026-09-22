# Plain-language workspace errors

Date: 2026-09-22

## Finding

Several signed-in workspace actions could display a raw database or service error directly to the customer. That could expose technical wording, internal field names, or provider details instead of explaining what happened and what to do next. Buyer checkout also prefixed raw service text with `Payment error`, even when checkout never opened.

## Change

- Routed seller, listing, offer-comparison, brokerage, and partner save errors through the existing customer-message filter.
- Replaced raw list-loading errors with short recovery instructions.
- Replaced internal identifier wording with “couldn’t find” guidance.
- Made buyer checkout failure copy confirm that no payment started and direct the customer to review the details and retry.
- Kept full technical errors in the browser console for diagnosis while removing them from the customer interface.

## Verification

- Regression coverage prevents the removed technical strings from returning to these customer-facing workspace paths.
- Existing customer-safe validation messages can still pass through the allowlist.
- No database, checkout, form, or deployment behavior changed.
- The correction is queued for the next intentional production bundle.
