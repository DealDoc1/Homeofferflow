# Lease source retrieval and private registration — October 20, 2026

Status: **source retrieval complete; TXR-1102 registered and database verified**.
This is not a customer workflow deployment or completed-signature QA claim.
Code baseline remains local `5f80b2e5`; documented production is `bfd03d99` /
shell v112. No code release, Vercel check or schema migration was needed.

## Source access resolved without owner action

The official Texas REALTORS library initially redirected to its normal NAR
login. A later visual check showed the browser's existing credentials had
autofilled, despite the earlier accessibility snapshot omitting their values.
One normal Sign In click succeeded. No password was read/exported/reset, no
terms were accepted, and no new access was granted. Do not report the source
session as an outstanding owner dependency or request another sign-in.

The authenticated `https://www.texasrealestate.com/forms-library` listed:

- TXR-2008, Addendum Regarding Lead-Based Paint: Active, English, October 14,
  2003. Its displayed download was `/api/documents/106/download`.
- TXR-2015, Addendum Regarding Rental Flood Disclosure: Active, English,
  September 1, 2025. Its displayed download was `/api/documents/25/download`.

Both normal download controls succeeded. Original downloads were copied without
alteration to the persistent private output folder, outside Git:

| Private source | Bytes | SHA-256 |
| --- | ---: | --- |
| `../lease-listing-2026-10-20/sources/TXR-2008-2003-10-14.pdf` | 144475 | `c6aaeefec282b09d5981a76326c1fd4e2a317ee6b4618184c16cf14b3e57372b` |
| `../lease-listing-2026-10-20/sources/TXR-2015-2025-09-01.pdf` | 171706 | `8a2439f6c191063a3abfe500d7a523e9fe9bb0265b03f663990e424ccedd3581` |

Both are one Letter-size page, with zero AcroForm fields and zero widgets.
Complete text and both full-page renders were inspected. TXR-2008 contains
landlord lead knowledge/report choices, tenant receipts and separate landlord,
listing-professional, other-professional and tenant execution lines. TXR-2015
contains two landlord flood-knowledge choices and separate landlord/tenant
execution lines. Those distinctions must remain in their adapters; do not
reuse sale disclosure geometry or infer tenant receipt. Supplier-added owner
contact imprints appear below the form footer and must be handled separately
from the original legal text, as for the listing source. Renders are under
`../lease-listing-2026-10-20/source-review/`.

## TXR-1102 private registration completed

Live read-only SQL confirmed only TXR-1101 was registered before this action.
The owner remains signed into the canonical HomeOfferFlow agent/admin account.
The saved QA wizard was exited without changing or accepting its unchecked
legal acknowledgement; its saved answers remain intact. The existing admin
library tool then uploaded the already authorized exact TXR-1102 source once,
using OnDemand Realty only as the existing source audit record. No brokerage
seat or new per-agent authorization requirement was added.

Visible success:
`TXR-1102 01-05-26 saved privately. Its workflow is not released for signing yet.`

Independent live SQL readback confirms:

- Source ID `562ded06-26f0-44e3-9162-a7895932b3cc`.
- Form TXR-1102, revision `01-05-26`, status `approved`.
- Exact 274481-byte file, SHA-256
  `30ae702ee94d71fc2aec5717f0d1b6d78b4fea53b5b418f7d74b39f658e44657`.
- Existing owner authorization attestation recorded by the authenticated API.
- Its private storage object exists; the `brokerage-form-sources` bucket remains
  nonpublic. Raw storage paths/URLs are not exposed in this evidence.

Receipt screenshot:
`../lease-listing-2026-10-20/source-review/TXR-1102-private-library-saved.jpg`.
The browser tab target was verified from the tab inventory/canonical hostname
before accessing admin controls. A form-label locator did not match; the actual
visible form IDs were used. No upload was retried or duplicated. The temporary
official source-library tab was closed after downloads; the owner's canonical
HomeOfferFlow tab remains open.

## Remaining implementation, not owner dependencies

1. Implement exact-source TXR-2008/TXR-2015 completion and signer maps, related
   package bindings and existing central-source intake support. The two files
   are downloaded locally, **not yet registered in the hosted library**.
2. Preserve landlord-completed facts and blank tenant acknowledgements when no
   tenant is selected; present the true preparation/signing state.
3. Complete changed-page ordinary/single-signer/Unicode checks and required
   provider-rendering QA, then the coordinated code/schema release and canonical
   production verification. Full regression remains a release-candidate step.

No signing request, email, customer message, new permission, billing change or
hosted schema write occurred. The only hosted write was the authorized TXR-1102
source/object registration through the existing admin endpoint. Broad roadmap
goal stays active; this source work does not establish lease launch readiness.
