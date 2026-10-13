# Current lease answers take precedence

## Scope and baseline

- User outcome: changing an interview answer must remove an unwanted lease/addendum/signer, even when an older saved offer carries historical aliases.
- Production baseline `9e23a6c3c8b6f749d5723137200bdfe1bc34da80`; READY `dpl_A93wp6sREXkqzhUuqDKtRj6wLkxP`. Scope is `lib/production_adapter.py` plus focused tests/evidence. Customer UI, Google autocomplete, source PDFs, verified renderer and signer geometry are unchanged.
- Ordinary protected CI and one intentional spend-guarded prebuilt release. No routine previews, live packet creation, email, payment, profile change, source-vault write or historical document replacement.

## Reproduction and behavior

- Five initial selection regressions reproduced three failures: current fixture No lost to the old fixtureLease Yes; current natural-resource No lost to old naturalResourceLease Yes; overall No leases still left old lease types and Seller-recipient requirements active.
- Centralize current-answer precedence. Explicit parent No suppresses all hidden type flags; a populated current type answer supersedes aliases/type labels. When newer answers are absent or blank, historical positive aliases/type labels remain supported. Current Yes also wins over an old alias No.
- The unchanged source renderer receives a private normalized copy using the same selected types as packet validation/assembly. Saved answers are not overwritten. Signer construction uses that same normalized choice; no field coordinate, role ID, width or height changes.

## Approved source, authorization and signing plan

- Existing approved public TREC 20-19, 05-04-2026; unchanged repository source `20-19_0.pdf`. Texas REALTORS lease sources and source authorization are unchanged. Owner/counsel's standing implementation/release authority applies.
- Active residential/fixture lease choices retain their existing approved forms, counterparties and parallel invitation plan. Natural-resource 4C remains on the main contract, not a separate addendum or extra signer. A deliberate No no longer resurrects old addenda/signers.
- Parent completed-provider visual evidence remains `purchase-provider-completion-2026-10-12.md`, document `6ad57745-57bc-4bd0-8324-e7d68b51c86e`. This batch does not claim a fresh executed lease-provider matrix or resend that unchanged parent plan.

## Rendered PDF QA and regression

- Eleven focused precedence tests pass; twenty controlled-purchase tests pass, including active lease paths and parent signer-map invariance. Actual no-lease packet with all historical Yes flags remains 12 pages; current natural-resource-only packet with a historical fixture Yes remains 12 pages, with no fixture render revision or Seller recipients.
- Both actual changed first pages were rendered at 120 DPI and visually reviewed: all lease boxes and the conditional termination blank stay empty for No leases; natural-only marks 4C/not-received and seven days, with 4A/4B empty. Printed three-day delivery text, source formatting, party/property data and signature geometry are unchanged. Both full generated packets contain zero field-tree entries and zero annotations.
- Compact unsigned intermediate review `/private/tmp/hof-lease-selection-review/changed-first-pages.pdf`. Generated packet digests: no leases `8df9117de4a8163c34757cc0ae5117f016ec8c0e068394480d328be32d0b9b77`; natural-only `4c8e923d26d2c6e099eb0fcd6bdde7fcb501a9f68e632e6a44d65333c79013b6`.
- Full candidate, independent CI, production identity and canonical runtime evidence are recorded after completion. This is not a full browser-to-Stripe/SignWell lease-matrix pass; those distinct roadmap gaps remain partial.
- Frozen full local candidate: 2,562 tests in 84.983 seconds, OK (one environment-dependent skip). Patch whitespace passes. Approved TREC source checksum remains `be3fa154f00476a674c73ba20f6c589111a905bc1e0894e0d5786b714f16f8d4`.
