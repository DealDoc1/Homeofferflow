# TXR-1101 sale-listing local implementation - October 17, 2026

Subsequent checkpoint: [private API integration](txr1101-private-api-local-2026-10-17.md)
is now locally implemented/tested. The steps below describe this earlier
renderer checkpoint, not proof of current deployment or completed signing.

## Batch contract and exact state

Intended user outcome: an agent answers a short listing interview, reviews a
source-backed sale-listing agreement and sends the correct parties one clean
package through the existing signing flow. This checkpoint implements its
answer contract, source overlay and signer geometry; **it does not complete
that end-to-end outcome**.

- Scope: new `lib/txr_1101.py`, dedicated tests and a local-only QA renderer.
- Last verified production baseline: 7b408eb09b46720261e8fed4712fe42e81547f33,
  release 39028545771. No code from this checkpoint is in production.
- Source: current English TXR-1101, printed 06-15-26, ten Letter pages,
  SHA256 eeec91ef481059834262cf7f842afc045bf17c09b5be9e79fe2508112310b068.
  See the [retrieval inventory](listing-agreement-source-checkpoint-2026-10-17.md).
- Cost: local-only work; no preview/build/deploy, API spend, new subscription,
  source upload, migration, invitation or customer record mutation.
- Complete-workflow evidence still required: interview/API integration,
  private source registration, authenticated ownership/review/send coverage,
  exact-provider completed-PDF QA and one coordinated intentional release.

## Implemented locally

- Explicit seller, property, listing term, negotiated compensation, protection
  period, MLS timing, Internet display, access, intermediary, financing,
  seller-entered exceptions, special provisions and document-list answers.
- No preset commission, inferred tax status, agent seat, source-owner or
  per-agent approval input. Unknown foreign-person status remains unanswered;
  integration must visibly present it for review rather than turn it into No
  or imply a finalized complete agreement.
- Reject hidden stale MLS/compensation terms and unsupported answers rather
  than silently dropping them. Preserve explicit zero compensation and reject
  precision loss, nonfinite amounts, invalid dates and mismatched signers.
- Source-specific blanks/checkboxes, repeated property headers and printed
  execution names. OnDemand's existing confirmed 9010832 broker-license
  fallback is reused; no new brokerage default is invented.
- Long/Unicode answers use the existing embedded-font and continuation tools.
  Overflow is lossless, identified by property/parties and referenced in 19Q;
  continuation initials follow the actual named signers.
- One/two sellers plus the deliberately selected broker OR associate sign on
  the printed execution rules, not printed-name rows. Separate date areas
  fit MM/DD/YYYY; footer initials fit inside measured underscore blanks.
  No signing-order setting is introduced.
- The original source is unchanged. Only the two supplier contact-imprint
  text operations are removed from cloned pages after exact source SHA and
  per-page text/hash/position/isolated-block validation. Copyright, form
  identification and all source clauses remain intact.

Checking a source document-list box is not proof another document has been
generated, attached, received or signed. Packaging integration must distinguish
those states and preserve the owner's instruction not to stop the listing
flow because a completed seller disclosure is not yet available.

## Local verification

Sixteen dedicated tests pass, including an opt-in actual-private-source
matrix. Combined with the related long-form/continuation/footer/imprint tests:
**36 tests, 9.923 seconds, OK**. No full regression was run for this partial
integration checkpoint; run it once on the eventual frozen release candidate.

Command (source path kept outside Git):

```sh
HOF_TXR1101_SOURCE=/path/to/private/TXR-1101-2026-06-15.pdf \
  /private/tmp/hof-account-context-qa-venv/bin/python -m unittest \
  tests.test_txr_1101 tests.test_txr_1501_renderer \
  tests.test_txr1501_overflow tests.test_txr1501_footer_initials \
  tests.test_txr_source_imprint -q
```

The actual source is reopened/rendered across eight fictional cases: ordinary
two-seller percentage fee; single seller/flat fee; broker signing and opposite
choices; delayed MLS; no MLS/single seller; additional fees/all financing and
document boxes; Unicode names/text; and one-seller multi-page overflow.
Seven remain ten pages; overflow has fourteen. Every source page's original
text, except the two member-supplier footer lines, is asserted to remain an
unchanged prefix after normalized whitespace, across all eight cases.

`scripts/render_txr1101_placement_qa.py` generates the eight local PDFs and
selected page PNGs. They are prominently labeled TEST ONLY / NOT SIGNED, and
blue widgets are local geometry guides, **not SignWell-rendered signatures**.
The original file inventory confirmed zero AcroForm fields/Widget annotations;
no interactive source was flattened or executed document altered.

Visual inspection covered ordinary pages 1-6, a fully populated page 7,
ordinary/all-checkbox/overflow page 8, both foreign-status choices on page 9,
ordinary/single-seller/Unicode execution page 10, delayed-MLS page 3 and
overflow continuation pages 11 and 14. Full continuation pages 12-13 and
remaining branch-specific pages are generated but not yet individually
visually reviewed. Do not expand this into an all-pages/all-provider pass.

Local QA corpus and manifest: `/private/tmp/hof-listing-qa-20261017/`.
Representative persistent image:
`txr1101-local-qa-2026-10-17/execution-placement-guide.png` under the chat's
visualization output root. All QA identities are fictional.

## Next implementation steps - no owner action needed

1. Integrate this contract/renderer/map with the existing private guided-form
   create/preview/review/send/status/download API. Reuse its identity, exact
   source revision and recipient-confirmation controls, without a seat gate.
2. Add the concise conditional listing interview and reuse saved seller,
   property and brokerage data/Google address completion. Clarify blank vs
   selected documents and handle unanswered tax status explicitly in review.
3. Register the source through existing private platform source maintenance;
   coordinate any required allowlist/constraint changes rather than activating
   an incomplete flow or applying an isolated behavior change.
4. Finish remaining branch/continuation visual review and actual completed
   SignWell QA, then run focused integration/full frozen-candidate checks and
   one spend-protected production release. Existing disclosure PR 1341 and its
   current test packet are separate; do not resend or bundle them accidentally.

TXR-1102 is retrieved but not implemented. The overall roadmap remains active.
