# TREC seller disclosure unsigned-preview QA - 2026-08-07

## Scope

The exact locally supplied seller-side source PDFs were rendered through the
current QA-only seller disclosure renderer. This review covers a populated
unsigned sample for every page of TREC-55-1 and TREC-61-0. It does not create a
SignWell document, send an email, or activate seller signing.

## Source verification

| Form | Revision | Pages | SHA-256 |
| --- | --- | ---: | --- |
| TREC-55-1 Seller's Disclosure Notice | 05-04-2026 | 4 | `65a52e167c290814930624ba230e232c152573359f1388cdb5e1237a62e4239a` |
| TREC-61-0 Seller's Disclosure About Groundwater and Surface Water Rights | 05-04-2026 | 2 | `91056ab6520af8cbef319986e03490f1bf6947817c3d3f563348f80f957f871f` |

The fingerprints match the source contracts in `lib/trec_seller_disclosure.py`.

## Visual review

- TREC-55-1 pages 1-4 rendered without clipping, page reordering, or source
  substitution. Property address, response letters, checkmarks, repair text,
  flood responses, additional disclosures, and seller/purchaser printed
  signature values remained on the intended source rows.
- TREC-61-0 pages 1-2 rendered without clipping or page reordering. Property
  address, groundwater/well responses, surface-water responses, and the
  seller/buyer printed signature values remained in the intended areas.
- The sample intentionally used two sellers and two purchasers so the second
  signer rows were exercised.
- No private storage URL, source path, or source metadata was written into the
  rendered PDFs.

## Gate status

The unsigned preview render gate is complete for the current field-map sample.
The forms remain preview-only. Before generation or signing can be enabled,
HomeOfferFlow still needs authenticated point-of-use QA, a document-specific
signer plan, controlled completed-signature visual QA, and release-authority
approval. Seller review links remain review/attestation-only until those gates
are separately satisfied.
