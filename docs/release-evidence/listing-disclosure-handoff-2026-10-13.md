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

## Completed application release

- PR #1330 https://github.com/DealDoc1/Homeofferflow/pull/1330. Exact head 8501e1ec74c621e510dd5f194a8210b811b5bfb5; independent CI 38488497027 passed, including 2,588 tests in 160.354 seconds (two environment skips), approved rendering, signer geometry, schema preflight and whitespace.
- Protected merge 83241c3fb51c01ec84d970d893a0d40d3aed8c5f. Exactly one intentional production release 38488908253 succeeded, with 2,588 merged tests in 128.168 seconds (two environment skips), coordinated schema, spend, prebuilt artifact and canonical PWA/API checks.
- Independently inspected canonical deployment READY dpl_G73wFGdW4brmkiAQ5HftCseJBpmY, homeofferflow-9jvjun0ir-dealdoc1s-projects.vercel.app, exact merge revision and www/root aliases. Actual canonical HTML matches the reviewed source byte-for-byte, SHA256 8ecada887f0007530b111640a925a06c9ef10bc05b08d68ab25adccd12d801dc. This proves served code, not a freshly completed customer or provider transaction.
- At 2026-10-14 00:16:36 UTC the real release guard counted nine preceding-24-hour deployments (limit 100), $0.03 infrastructure credit used, $19.97 unconsumed and unchanged $3 reserve for September 22-October 21. Snapshot, not a future cost guarantee or total invoice.
- Bounded error/fatal sample 00:17:02-00:18:24 UTC found no records. No extra deployment, real packet, email, charge, signing acceptance or new permission was created.
- Prepared one-row roadmap reconciliation and two focused tests. The connector write returned Invalid or expired requestState; independent readback proves the roadmap record is unchanged. Do not claim that metadata correction was applied. The local SQL remains prepared for an authenticated operational path.
- Final interactive in-page choice completion remains unverified because obsolete native-confirm preview tab 29 blocks browser clicks. A concise nonblocking owner request to dismiss/close it was issued; do not treat a goal continuation as proof it was dismissed. Preview server PID 46214 was identified and stopped with TERM, exit 143 confirmed. New preview tab 33 should be closed when finishing; exact pre-existing fictional SignWell tabs 24/25 remain handoffs, not newly sent requests.
- Owner explicitly selected completing and publishing all three Integrity First placements as the next workstream. Overall roadmap goal remains active.
