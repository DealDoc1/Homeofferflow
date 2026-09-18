# Mineral reservation in the purchase interview - September 18, 2026

## Status

Local implementation and local browser-to-PDF verification only. Not pushed,
deployed, or production-verified. No SignWell request or customer email was sent.
The TXR-1905 source geometry still needs completed-provider verification; this
work does not refresh either approved map baseline or claim release readiness.

## User outcome

The purchase interview now asks whether the seller will reserve mineral rights.
If selected, it asks for all versus an undivided percentage and the surface-rights
election. It reuses the purchase address, buyers, and shared seller contacts.
There is no separate form-source upload, brokerage-seat requirement, or approval
step for an agent. The review lists the form, percentage, surface election, and
the actual seller signing scope.

The same generated purchase PDF includes TXR-1905 after the existing lease and
hydrostatic documents and before user uploads. Paragraph 22 checks its actual
mineral-addendum cell. Buyer recipient IDs remain 1/2 and seller IDs 3/4 for all
one/two-buyer and one/two-seller combinations. A single SignWell payload contains
the whole packet and uses simultaneous invitations. Seller acceptance of the
purchase contract is not silently added when only a mineral addendum is chosen.

## Implementation

- Private source retrieval extends the existing request-only source envelope.
  Existing exclusions prevent its PDF bytes from entering saved answers,
  browser storage, email JSON, or customer-answer billing hashes. The existing
  source lookup remains platform-wide, not filtered by an agent's brokerage.
- The source SHA-256 is pinned to the actual privately supplied 11-07-2022 form:
  `79f6b8e8b4faa8293abddf4e298f39dbaada703919812c01726c9721af5b0cf3`.
  A changed source cannot be rendered against this calibrated map silently.
- The exact source hash and renderer revision participate in signing identity.
  Coordinates are reused from the TXR-1905 local source-placement candidate;
  this integration changes absolute page numbers and recipient IDs, not its
  relative signature coordinates.
- Explicit source elections are required; there is no guessed default. Partial
  percentages must be greater than zero and at most 100, with up to four decimal
  places. Selecting all minerals discards a stale percentage from packet data.
  Deselecting the addendum clears both selection aliases and its terms.
- Long answers preserve the renderer's continuation and initial fields; page
  offsets account for those pages before assigning upload signature fields.
- Shared buyer/seller checks reject missing names, unpaired second signers,
  malformed or duplicated email addresses, and conflicting temporary-lease
  seller identities. A deselected lease's contacts cannot override current ones.

## Evidence

Ten new backend tests exercise the four-party matrix, exact contract checkbox,
source hashing, absent/changed-source rejection, validation before rendering,
continuations, mixed lease/hydrostatic/upload packets, legacy selection,
simultaneous one-file signing payload, and private source hydration. CI uses an
explicitly hash-substituted blank source, not committed private form bytes.

Sixteen actual JavaScript runtime tests pass, including five mineral cases for
validation, conditional fields, shared sellers, clearing hidden terms, saved
draft restoration, review summaries, escaping, and seller signature scope.
The existing unrelated checkout/restore test harnesses now include the new
validation/visibility dependency; their original assertions are unchanged.

Final full discovery: **2,141 tests in 37.766 seconds; 2,139 passed and the two
existing approved-map baseline comparisons failed.** Those are the pending
TXR-1507/1905/1914/1919 candidate-map differences recorded previously, not new
integration failures. This is not an all-green release result. Log:
`/private/tmp/hof-mineral-packet-suite-final.log`.

Used the browser verification and PDF skills for local checks. The dedicated
agent-browser CLI was unavailable, so the connected browser controlled one
temporary localhost tab. The local QA bridge extracts the actual interview
markup, helpers, and collector and invokes the real production packet builder.
It never calls authenticated production generation, payment, email, or signing
services. Four synthetic packets were generated:

1. 25.125% reserved, surface rights waived, one seller: 13 pages, addendum
   signatures on page 13 for recipients 1 and 3.
2. All minerals reserved, surface rights retained, two sellers: 13 pages,
   signatures on page 13 for recipients 1, 3, and 4; hidden percentage cleared.
3. Addendum deselected: 12 pages, no mineral fields, selection aliases and terms
   cleared from submitted packet answers.
4. Rebuilt the all-minerals packet after ensuring the address uses the same TX
   default as the purchase contract; 13 pages.

Inspected the rendered Paragraph 22 page and the selected mineral pages for
partial, all, and final address-consistent outputs. Checkbox marks occupy the
intended cells, the percentage is legible with its percent sign, and signature
blanks contain no draft names. These are unsigned PDFs, not provider-completed
signature evidence. Unchanged purchase pages are covered by existing regression
checks, not claimed as a fresh page-by-page visual audit here.

Browser UI reported successful local generation. No application exception was
observed during the tested actions. The console did contain one connection
message ('Receiving end does not exist'); therefore no zero-console-error claim
is made. The temporary tab was closed and the localhost process stopped.

Private outputs are untracked under `tmp/pdfs/mineral-browser/`. No source PDF,
customer PDF, signature image, key, or credential is included in this commit.

## Remaining verification and release limits

Authenticated generation through the live private source store, completed
SignWell mineral signatures, mixed live packet execution, and deployment remain
unverified. This does not close the other financing/assumption/environmental
combined-packet items or the remaining TXR-1507 signer-variant QA. No Vercel
build, preview, deployment, paid integration, or public Git push occurred.

Supabase storage guidance was checked before extending the existing lookup:
https://supabase.com/docs/guides/storage/serving/downloads . The current changelog
showed no relevant new storage-download breaking change; no schema, RLS,
permissions, subscription, or service credential was changed.
