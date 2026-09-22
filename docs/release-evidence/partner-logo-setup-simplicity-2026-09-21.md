# Partner logo setup simplicity — 2026-09-21

## User problem

Partner setup presented two logo methods: a normal image upload and a technical
"secure logo URL" field. The second choice exposed implementation language,
created an unnecessary decision, and contradicted the managed upload path the
product already provides.

## Candidate change

- Present one customer-facing logo action: upload an optional PNG, JPEG, or
  WebP image up to 2 MB.
- Preserve an existing saved logo privately when the partner does not choose a
  replacement image.
- Replace the internal "CTA" label with the plain-language "Directory button
  text."
- Replace the technical upload fallback with a normal retry message.
- Add no dependency, vendor service, or recurring cost.

## Verification

- Focused partner self-service onboarding suite: 26 tests passed.
- Full repository suite: 2,396 tests passed in 68.060 seconds.
- A 390 by 844 headless Chrome check confirmed the single upload choice,
  existing-logo guidance, private saved-logo state, plain-language button
  label, absence of the URL choice, and zero page-script errors.
- Deterministic production manifest: 142 files / 21,228,434 bytes, 111 bytes
  smaller than the preceding release candidate.

## Release status

Implemented, locally tested, and browser-verified. This improvement is not
production-live until it is merged and included in the coordinated post-reset
deployment, followed by canonical partner-setup verification.
