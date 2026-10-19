# Reviewed disclosure in the listing signing package

## Bounded outcome and release baseline

Include the seller-owned, completed disclosure in the existing TXR-1101 listing
signature request, without blocking other documents when it is unfinished.
Scope: optional interview selection, owned adapter, packet composer, existing
delivery checkpoint, database version binding and frozen-draft UI. No app,
billing, new permission, customer packet or external communication.

Production remains `61e516d0a091646bbff14a00624051d4e328d4fc`, deployment
`dpl_2agZyywm1ahG4Pk5tjdaWdZ3YfVx`. Automatic Git deployments remain disabled.
No Vercel build/deployment or production database write occurred in this batch.

## Implemented locally

- The listing interview stores only an explicit disclosure draft UUID. Selecting
  a reviewed disclosure also selects its water notice when present; answers are
  neither copied into the listing nor guessed.
- The adapter requires the current owner, matching property and identical seller
  parties, current saved complete answers and each seller's current confirmation.
  It handles reversed recipient order and Unicode names explicitly. Stale,
  separately sent or unavailable disclosures are honestly pending.
- Main notice, water notice and continuation pages use the existing source-aware
  renderer and field maps. The composer appends their PDF/fields once, preserves
  page offsets and fingerprints the reviewed content and signature mapping.
- The existing listing delivery checkpoint atomically binds that disclosure
  version before a provider request can proceed. Database guards reject forged,
  foreign, stale or reassigned bindings. Frozen disclosures cannot be edited or
  independently sent; corrections require a new draft. Ordinary listing writes
  without a disclosure binding retain their prior behavior.
- API and schema readiness are coordinated through migration
  `20261019000034_bind_disclosure_to_listing_signature.sql`. No RLS/grant
  expansion or new signing queue was added.

## Evidence

- Final affected workflow run: **230 tests passed**, no skips, 14.340 seconds,
  with `HOF_TXR1101_SOURCE` set to the actual supplied source. Includes owned
  adapters, packet/page/recipient mapping, API send/retry, questionnaire/review,
  disclosure signing boundaries, JavaScript interview runtime, schema readiness,
  shared delivery coordinator and existing PWA/companion regressions.
- Isolated real PostgreSQL: **67 assertions passed** against actual migrations,
  including client forgery, stale binding, immutable sent content, ownership,
  another packet, and edit-first/send-first races over independent connections.
  No TCP listener or production credentials; cluster shut down after the test.
- Actual-source, isolated-transport fixtures: one seller (14 pages/24 fields),
  two sellers plus water (16 pages/43 fields), Unicode continuation (17 pages/45
  fields). Changed main execution, water initials/execution and continuation
  pages were visually inspected. These unsigned blue-field guides are **not**
  completed SignWell placement proof.
- Desktop and 390x844 phone selector reviewed; document width equals 390px.
  Selected UUID and automatic B/P checklist selection verified from rendered UI.
  Screenshots: `listing-disclosure-packet-2026-10-18/desktop-picker.png` and
  `listing-disclosure-packet-2026-10-18/mobile-picker.png` in the chat output root.
- Supplied flattened 55-1 SHA256 `65a52e167c290814930624ba230e232c152573359f1388cdb5e1237a62e4239a`
  and current official fillable download SHA256
  `cebab031402fef2d1a16b91e6820b778f3e8971764177700706ec3f6ad8f359b`
  have identical full-page pixel hashes on all four pages at 108dpi. Both pages
  of supplied/current official 61-0 also render identically. The existing
  flattened source pins remain unchanged; no source-owner action is needed.

## Remaining, not a claim of release

Complete the retained v4 full-disclosure signed-provider visual check and v2
listing-lead provider QA. Then freeze the integrated release candidate, run
the full regression once, apply dependent migrations and code together, make
one intentional release after checking current headroom, and verify canonical
live behavior. Purchase-offer packet integration remains separate from this
TXR-1101 listing adapter. No new owner action is needed for this checkpoint.
