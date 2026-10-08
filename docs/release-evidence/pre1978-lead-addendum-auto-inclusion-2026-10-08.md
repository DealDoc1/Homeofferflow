# Pre-1978 lead addendum auto-inclusion — 2026-10-08

## Intended user outcome

Do not stop a buyer's supported offer because a completed seller disclosure is
not yet available. When the home is known or possibly built before 1978, include
the blank TREC Form 56-0 in the buyer packet so the transaction can proceed;
do not invent or pre-select the Seller's disclosure answers.

## Source and authorization

- Form: TREC Form 56-0, revision printed 05-04-2026.
- Local source: `lead_based_paint_56-0.pdf`.
- SHA-256: `eb8bdfb943cafbe8402e6b44fe44d73eb66d6acd6a99f31f73498f938fd76e6c`.
- The owner explicitly authorized use of the supplied Texas forms for
  HomeOfferFlow. The blank form remains for the appropriate parties to
  complete; HomeOfferFlow does not select Seller disclosure answers.

## Changed behavior

- Known pre-1978 and unknown-year buyer offers include blank Form 56-0 even
  when no completed Seller disclosure was uploaded.
- If a completed Form 56-0 is supplied, it replaces the generated blank and is
  included once.
- Newer homes do not receive an unneeded lead addendum.
- Buyer and buyer-agent signing fields are placed on their printed execution
  lines. The Seller and Seller's broker areas remain blank in a buyer offer.
- The completed disclosure upload is optional and no longer blocks packet
  generation.

## Local verification

- Focused packet and upload workflow suite: 20 tests passed on 2026-10-08.
- The full repository suite passed 2,469 tests on the unchanged product-code
  candidate before a one-buyer regression test was added; that added test is
  included in the 20-test focused pass above.
- A synthetic two-buyer packet was visually inspected at 13 pages. Buyer 1,
  Buyer 2, and buyer-agent fields align with the printed rules; Seller
  disclosure and buyer acknowledgment boxes remain blank.
- A synthetic one-buyer packet was visually inspected at 13 pages. It exposes
  only Buyer 1 and buyer-agent signing fields on their printed rules, with no
  Buyer 2 fields. See the local render at
  `/private/tmp/hof-lead-one-buyer-20261008/one-buyer-1.png`.
- The single-buyer field regression asserts the exact recipient IDs, page, and
  coordinates. `git diff --check` passes.

## Provider QA and release state

- No SignWell test document was sent or completed in this pass. The current
  Mac/browser session is locked, preventing authenticated upload and retrieval
  of a completed test PDF.
- Completed-provider PDF inspection is therefore **not yet verified**; local
  rendering is not a substitute for the SignWell-completed artifact.
- This candidate is locally implemented and tested, and locally visually
  reviewed. It is **not deployed or production-verified**.
- Before release: restore authenticated SignWell access, complete the
  nonbinding test with the approved QA inboxes, inspect every page of the
  completed provider PDF, then confirm Vercel headroom and run the intentional
  production-release workflow.

## Code checkpoint

- Branch: `codex/lead-addendum-auto-attach`.
- Product-code commit: `052e674a9b98d2aed2eeb98d9dfa018eea87470a`.
- The one-buyer regression test and this evidence update are subsequent local
  changes and have not yet been committed.
