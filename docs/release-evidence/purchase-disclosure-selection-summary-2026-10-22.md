# Purchase disclosure selection summary — October 22, 2026

## Customer outcome

Before generating an offer packet, the offer screen identifies the selected
seller-reviewed disclosure by property and names the Sellers who sign and
Buyers who acknowledge receipt. The same concise summary appears beside the
selection and again during offer review.

## Implementation and validation

- Reused the saved, owner-scoped summary returned by the existing preview flow;
  no new API or database fields were added.
- Displays recipient names and roles only. Recipient email addresses,
  disclosure PDF bytes, and other private preview content are not rendered.
- Uses `textContent` for the property and names, retaining safe output for
  user-provided values. A summary saved for another account remains hidden.
- Versioned the helper asset and advanced the offline shell to v123 so
  installed clients fetch the updated selection UI.
- Focused validation: 56 tests passed across the saved-disclosure picker,
  preview API, purchase generation/delivery, and PWA cache behavior.
- Full local regression on the updated candidate: 2,932 passed, 23 skipped.
- Visual review used fictional offer/disclosure data with the actual UI helper
  at desktop and 390×844 mobile. Property, Seller, and two Buyer names wrapped
  readably; no horizontal overflow. Both the attachment-selection summary and
  the offer-review summary were checked. No production API was called.
- `git diff --check` passed. No database changes, customer documents, messages,
  signing requests, or external writes occurred.

## Release status

Implemented locally, tested, and visually reviewed; not deployed or
production-verified. Automatic Git deployments remain disabled. The full
candidate regression and release cost checks remain required before a release.
