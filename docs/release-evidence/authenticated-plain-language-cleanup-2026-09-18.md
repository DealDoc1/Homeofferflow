# Authenticated plain-language cleanup — September 18, 2026

## Outcome

HomeOfferFlow's authenticated entry and account surfaces now describe the
customer's next action instead of exposing internal “workflow” language. The
cleanup covers role selection, missing-document requests, buyer guidance,
packet pricing, billing-limit recovery, agent activation, brokerage setup,
seller-lead classification and partner-placement descriptions.

Examples include “Repeat-offer workspace,” “Which form or document do you
need?”, “Guided buyer-offer questions,” “Seller lead type,” and “Document,
signing, or account support.” References to SignWell were removed from generic
help copy because customers need signing help, not provider implementation
details.

No event names, API fields, database values, transaction choices, prices,
entitlements, checkout behavior, form mappings or signature behavior changed.

## Verification

One hundred five focused tests pass across low-noise copy, missing-form intake,
agent activation, subscription checkout, partner tiers and brokerage
activation. Patch whitespace is clean.

This is **locally implemented and tested, not deployed or production visually
verified**. It adds no dependency, provider request, database work or recurring
cost.
