# Unreachable overlay cleanup — 2026-09-21

## User problem

The homepage bundle still contained two older overlays that no current link,
button, route, or workflow could open: a duplicated Terms summary and a
buyer-agent sales pitch. Their unused handlers, referral-message utilities,
and styling added noise, retained stale legal and marketing copy, and created
future accessibility and copy-drift risk without providing a customer action.

## Candidate change

- Remove the unreachable duplicated Terms overlay and its unused open, close,
  and backdrop handlers.
- Remove the unreachable buyer-agent pitch overlay, its unused choice handlers,
  and its private styling.
- Preserve direct links to the current Terms, Privacy Policy, Disclaimer, and
  E-Sign Consent pages.
- Preserve the active subscription-consent dialog, its dialog semantics, and
  the transaction interview's current agent-choice flow.
- Reduce the production bundle by 9,461 bytes relative to the prior candidate,
  with no new dependency, vendor service, or recurring cost.

## Verification

- 50 focused homepage, SEO, interview, audience-routing, and regression tests
  passed after updating the test boundaries that had used the dead overlay as
  a source-code delimiter.
- Full repository suite: 2,395 tests passed in 69.533 seconds.
- A 390 by 844 headless Chrome check confirmed both legacy overlays are absent,
  all four current legal links remain, the guided buyer interview opens with
  `aria-hidden="false"`, focus moves into the interview, and no page-script
  errors occurred.
- Deterministic production manifest: 142 files / 21,228,545 bytes.

## Release status

Implemented, locally tested, and browser-verified. This cleanup is not
production-live until the coordinated post-reset deployment completes and the
canonical homepage and guided offer entry are checked again.
