# Listing to seller-disclosure handoff

## Batch contract

- Outcome: reuse the signed-in agent's sale-listing property and seller names in the existing disclosure interview without overwriting current disclosure work.
- Scope: listing next-step card and saved-listing action, owner-scoped disclosure handoff, in-page replacement choice, mobile field sizing and PWA shell v95. No PDF, signer map, legal wording, pricing, billing, new source form or permission changes.
- Verified production baseline: a63489823e2d823aa2835ecb3d7e3a1db97b5b52, READY dpl_FiQvp354oPnUfwoCtMw6DuCAkp8x. Automatic Git deployments remain disabled. One guarded prebuilt release is intended, not yet dispatched.
- Cost: no paid QA, customer send, payment or duplicate deployment. Existing $3 infrastructure-credit reserve is unchanged.
- Completion proof: actual-source runtime cases, desktop/phone fixture rendering, full regression, independent exact-head CI and canonical deployment verification.

## Implemented and tested locally

- Newly saved listings offer Question 3: prepare a seller disclosure or continue with planning. Lease listings retain lease planning without a sale disclosure. Existing sale-listing rows also expose the disclosure action.
- The handoff reads one current listing by both listing ID and agent ID. It verifies returned ownership and ignores stale requests, replaced cards and changed identities. No mutation, document creation, review attestation, email or signing request occurs merely by opening it.
- Property and one/two seller names carry forward, including Unicode. Three sellers are not silently truncated. Emails, buyers and disclosure answers are not inferred.
- Existing saved/current disclosure work has an in-page Keep current disclosure / Start new disclosure choice. Keep has default focus, Escape cancels and Tab is bounded to the choice. Explicitly starting another clears only the on-screen draft identifiers/answers; saved records remain unchanged. Identity and in-flight save state are rechecked before replacing fields.
- Actual-source Node runtime: 19 passing cases. Affected Python workflow/PWA checks: 111 passing tests.
- Frozen full local suite: 2,588 tests in 114.401 seconds, OK with one environment skip. The expected negative-fixture diagnostic `ERROR: Invalid fixture PDF` follows the successful result and is not a test failure.
- Independent live SQL confirms listing RLS enabled and SELECT policy limited to authenticated agent_user_id = auth.uid(). No grants or policy changes.

## Browser evidence and boundary

- Localhost-only fixture runs the real disclosure script, real next-step functions and stylesheet with an explicit fictional owner/row/source. No authenticating credential or external customer mutation is present. Not a real production save or completed-provider test.
- Initial desktop click carried the listing ID, property and Ana García / Wei Chen into the real disclosure fields and opened the interview. Source form and Google address behavior are unchanged.
- Mobile review reproduced 533px content in a 390px viewport. Corrected the disclosure grid/input/select minimum and maximum widths; subsequent DOM read and screenshot confirm width 390px with the same property and seller values.
- Final in-page replacement choice was visually rendered at 390x844. Browser click completion was not proven: an earlier obsolete native-confirm preview remained stuck in the browser's focus command. The replacement choice's actual handlers, cancel, reset and account-change behavior are proven by the 19 runtime cases, not falsely described as an interactive production pass.
- Screenshots: /private/tmp/hof-listing-disclosure-desktop.png, /private/tmp/hof-listing-disclosure-mobile.png, /private/tmp/hof-listing-disclosure-choice-mobile.png. These are local fictional previews.

## Checkpoint

- Owner asked for Integrity First launch status/screenshots before this batch was released. Runtime is locally implemented/tested; no PR, merge or Vercel release is claimed yet. Keep the full roadmap goal active.
- Live Integrity First readback remains qualified / beta / onboarding in_progress / agreement not_started, with no placement rows. Canonical roofing API independently returns ok true and partners empty. A saved logo is not publication.
