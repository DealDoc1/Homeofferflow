# Listing-agreement source checkpoint - October 17, 2026

## Bounded batch

- Outcome: source-backed sale and lease listing interviews using the actual
  current English TXR-1101 and TXR-1102 PDFs.
- Scope: source discovery and revision verification only; no renderer,
  interview, signer-map, access, billing or database changes in this batch.
- Production baseline: main 7b408eb09b46720261e8fed4712fe42e81547f33,
  intentional release 39028545771. This checkpoint does not change production.
- Cost constraint: no preview, paid-service change or documentation-only release.
- Completion evidence: obtain actual current source PDFs, inspect their printed
  revisions and geometry, then implement and test a separate coherent batch.

## Verified source facts

The owner-supplied `all TXR forms available.pdf` is a 13-page catalog saved
July 28, 2026, not the listing agreements themselves. Complete relevant pages
1 and 3 were extracted and inspected. The catalog lists:

- TXR-1101, Residential Real Estate Listing Agreement, Exclusive Right to Sell:
  revision June 15, 2026; official downloader post_id=3711.
- TXR-1102, Residential Real Estate Listing Agreement, Exclusive Right to Lease:
  revision January 5, 2026; official downloader post_id=3712.

Those are catalog revision dates, not a claim that no later revision exists.
The official current download page must establish the source actually used.
Catalog annotations point to the normal authenticated form-downloader route;
the Spanish/Vietnamese links are not substitute English execution sources.

A filename-scoped PDF search of the supplied iCloud HomeOfferFlow folder and
the original Documents/HomeOfferFlow repository returned no TXR-1101,
TXR-1102 or listing-agreement PDF. This is not a claim about every file on the
owner's computer. Earlier source-catalog checks recorded no shared 1101/1102
entry; no new database query or change was needed for this file/access check.

## Download-session dependency resolved in this batch

Opening the official blank-form downloads page in the existing built-in
browser on October 17 redirected to the National Association of REALTORS
sign-in page at realtors.auth0.com. Its first accessibility snapshot did not
report values. Subsequent visual inspection showed existing credentials had
autofilled. One normal Sign In click succeeded without reading or exporting
the password. No reset, CAPTCHA, new terms, access bypass or purchase occurred.

The authenticated library is now https://www.texasrealestate.com/forms-library
and displayed the owner's member identity. Both English listing forms were
listed Active with the same dates as the supplied catalog. Their visible
Download controls used /api/documents/183/download (1101) and
/api/documents/182/download (1102). Both source PDFs were downloaded normally.
The first browser download returned exceptionally slowly. The second browser
download event timed out, but its file had actually completed; the file was
inspected rather than downloaded again.

There is no outstanding owner sign-in/source-file action for these two forms.
There is no source-owner, brokerage-seat or per-agent approval requirement.
Existing HomeOfferFlow active agent access was separately visible and must
not be described as signed out.

## Retrieved source inventory

Copies retained outside Git under the persistent chat visualization root:
`listing-source-2026-10-17/sources/`.

- `TXR-1101-2026-06-15.pdf`: 235868 bytes; 10 Letter pages; printed revision
  06-15-26; SHA256 eeec91ef481059834262cf7f842afc045bf17c09b5be9e79fe2508112310b068.
- `TXR-1102-2026-01-05.pdf`: 274481 bytes; 11 Letter pages; printed revision
  01-05-26; SHA256 30ae702ee94d71fc2aec5717f0d1b6d78b4fea53b5b418f7d74b39f658e44657.

Both reopen with pypdf; both have zero canonical AcroForm fields and zero
Widget annotations. They need source-coordinate overlays and signer maps,
not an assumed native-field fill. The official download adds the owner's
member/brokerage contact footer; inspect and handle it deliberately during
source/render integration. Do not commit private source PDFs to the repository
or expose raw source URLs in the customer browser.

Screenshot:
`listing-source-2026-10-17/official-current-listing-forms.jpg` under the persistent
chat visualization output root.

Source retrieval is complete. No listing workflow was implemented, tested for
signing or deployed in this batch. Existing production workflows are unchanged. Pending disclosure
candidate PR 1341 and its existing provider test remain separate and untouched.
