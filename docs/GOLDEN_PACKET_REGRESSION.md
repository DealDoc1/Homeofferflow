# HomeOfferFlow Golden Packet Regression Suite

The automated suite in `tests/test_controlled_launch.py` protects the supported
TREC 20-19 production packet shape, addendum order, and required buyer signing
fields. It is a safety net, not a substitute for visual completed-PDF review.

## Scenarios

| # | Scenario | Primary regression guard |
|---:|---|---|
| 1 | Cash, one buyer | 12-page base packet and one buyer signer |
| 2 | Cash, two buyers | Second buyer signer appears only when needed |
| 3 | Conventional, one buyer | Two-page financing addendum and signer |
| 4 | Conventional, two buyers, repairs/warranty/concession | Two-buyer financing signer plan remains intact |
| 5 | HOA | HOA addendum and signer placement plan |
| 6 | Appraisal partial waiver | Financing plus appraisal addendum order and signer plan |
| 7 | Sale of Other Property | Sale addendum and signer plan |
| 8 | Backup Contract | Two-page backup addendum and signature-page signer plan |
| 9 | Seller's Temporary Residential Lease | Four-party Buyer/Landlord and Seller/Tenant signing order and placement |
| 10 | All supported addenda | 20-page stress packet and all major addendum signer plans |
| 11 | Sparse optional fields | Base packet remains valid without optional values or addenda |

## Required checks

Run the full test suite before every deliberate production release:

```text
PYTHONPATH=/private/tmp/homeofferflow_test_deps \
/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
-m unittest discover -s tests
```

For changes that affect PDF field coordinates, source forms, addendum assembly,
or SignWell placements, also generate and visually inspect the applicable
rendered packet and completed signed PDF. Keep previously passed coordinates
locked unless the rendering proves a regression.

## Out of scope

These scenarios cover only currently supported buyer-side purchase packets and
their implemented addenda. They do not authorize or imply support for blocked
TXR source-gated forms, seller-listing documents, or any other form workflow
without its separate source, signer-plan, and visual QA gates.
