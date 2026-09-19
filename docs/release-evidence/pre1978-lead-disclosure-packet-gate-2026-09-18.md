# Pre-1978 lead disclosure packet gate — 2026-09-18

## Outcome

- The purchase interview now asks for the completed seller/listing-side lead-based paint disclosure in the same section as the pre-1978 question.
- A pre-1978 offer cannot continue to checkout or packet generation until the user confirms receipt and attaches the PDF.
- An unknown construction year cannot proceed until it is confirmed.
- The production adapter independently enforces the same requirements, checks the Paragraph 22 lead-disclosure item, and appends the uploaded PDF exactly once.
- HomeOfferFlow does not generate a blank lead disclosure or invent seller disclosures.
- An uploaded disclosure does not add an unnecessary agent signing recipient or assume signature coordinates for an unknown uploaded form.

## Verification

- 70 focused Python packet, production-adapter, delivery-recovery, and SignWell-bounds tests passed.
- 109 browser-runtime interview, upload-isolation, draft-resume, and Step 3 navigation tests passed.
- The focused packet test verifies a 12-page purchase contract plus one uploaded disclosure, the Paragraph 22 checkbox data, and no duplicate generated lead form/signature fields.

## Current release state

- Implemented and locally tested.
- Not yet deployed or production-verified.
- The exact latest production offer row could not be inspected during this run because the Mac was locked and the authenticated Chrome tab was unreachable. The live record must be checked after unlock before any existing packet is modified or resent.
