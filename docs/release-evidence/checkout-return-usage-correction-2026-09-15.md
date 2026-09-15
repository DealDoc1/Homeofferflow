# Checkout-return packet usage correction

## Reproduced behavior

`showPaymentSuccess` previously called `saveOfferDraftToSupabase('Generated')`,
logged a payment-success offer event, and requested a `signed_packet` usage
event for any non-homebuyer when a browser-only subscription flag was false.
That branch ran even with `checkoutConfirmationPending: true`. Thus the same
function correctly displayed unconfirmed checkout while incorrectly attempting
generated-status and usage writes. A copied or repeated return page could
reach this branch. This is an offline reproduction, not an assertion that a
specific production customer lost allowance.

The Node regression executes the real display function with four role labels
and three response states, with the subscription flag false. Before the fix,
nine of the twelve combinations recorded all three unintended effects: agents,
investors, and brokerage administrators under pending, unknown, and generated
states. Homebuyer cases did not execute the legacy branch.

## Local correction

Removed fulfillment writes from this presentation function completely. Neither
role, a browser return parameter, an in-memory flag, nor a repeated render is
evidence that a packet was generated. The existing authenticated subscriber
generation handler retains its separate generated-offer and usage flow after
the API response. The paid checkout webhook still prepares its saved record.
No usage schema, entitlement, subscription, quota, or billing setting changed.

All twelve role/state combinations now produce no generated-offer, offer-event,
or usage writes from the display function. Existing runtime tests confirm
subscriber API success and email-pending responses still record their normal
generation usage once per invocation, while a genuine server error records
none. This does not prove idempotency across multiple generation invocations.
No markup or visual layout changed in this correction.

## Remaining usage-contract work

The server `usage_event` action currently validates entitlement and optional
offer ownership, then inserts a row; the caller still supplies billing month
and quantity, and no generated-packet identity deduplicates that write. The
generation preflight and usage insert are not one atomic reservation. Fixing
that requires a server-owned generation/usage identity and database-enforced
deduplication; do not describe this display-only correction as complete quota
or concurrency protection. Keep this next in the usage-management work.

## Release and QA

Full local regression: **1,933 tests pass**; `git diff --check` passes.

The verification skill guided the boundary reproduction before editing.
This correction is local only and must be bundled with the pending release.
No production data was edited, no emails or signing invitations were sent,
and no Vercel build or deployment was requested. Historical usage is not
changed or refunded automatically without verifying the exact affected rows.
