# Guided-form presentation and relevant guidance — September 10, 2026

## Observed problems

- In a real production guided-form dialog, the computed background was
  transparent because `--navy-dark` was undefined. Form inputs inherited black
  browser-default text, a 13.33px font, and a 17px height. The prior simplified
  local recipient fixture overrode those styles and therefore missed this.
- Agent transactions displayed a concession tip that began by saying the
  user had no buyer's agent. A conditional-section refresh could also hide
  agent details by reading a hidden, unselected homebuyer-only radio group.

## Corrections

- Shared dialogs use the existing opaque navy theme, readable white 16px input
  text, at least 44px controls, properly sized native checkboxes/radio buttons,
  and dark select options. No extra customer questions or consent steps.
- Grid tracks can shrink, long labels wrap, mobile actions stack, and dialogs
  remain vertically scrollable within the available viewport.
- Only explicitly unrepresented homebuyers/investors see the existing
  unrepresented-buyer tip. Agent details remain visible on agent transactions
  when other conditional answers refresh. The actual concession options and
  financial/legal wording are unchanged.
- Service worker cache version advances to v66 for the next release.

## Verification

- 1,625 local tests pass, including six new style/behavior regressions and
  nine executed representation-choice scenarios. All 43 inline scripts parse;
  patch whitespace is clean.
- The local browser fixture now includes all actual production style blocks
  plus the actual recipient-dialog implementation. It uses synthetic names
  and example.com addresses; no real email or provider calls are possible.
- At a 1280px browser viewport, the dialog computed to an opaque
  `rgb(13, 31, 53)` background; both recipient inputs had white text, 16px
  font size, and 48.39px height. Dialog client and scroll widths both measured
  758px, with no internal horizontal overflow.
- Visually inspected the same dialog in a 375px-wide local iframe: both
  recipients, full email field, Cancel, and Send signature request fit and are
  legible. Buttons stack and content does not clip horizontally. This is a
  constrained browser layout test, not an iOS/Android device test.
- Refreshed the existing completed TXR-1507 current-release QA document in
  production. Its HomeOfferFlow status changed from sent to signed, matching
  SignWell, and Download completed PDF became available.

## Release boundary

This presentation batch is locally verified and not yet deployed. It does not
change form editions, PDF coordinates, signers, database schema, checkout,
permissions, or Google Maps autocomplete. Current production remains
`088147cdfed2919a1aa02cb3988b2097b66ae7ce` with the verified complete recipient
preview and successful live TXR-1508 send. The TXR-1508 completed-PDF placement
check still awaits the user's signatures.
