# Seller-disclosure explanations and combined-packet assembly

## Bounded outcome

Carry the Seller's literal explanations from the private interview through
save/reopen to the source PDF without silently discarding or truncating them.
Scope: disclosure interview, existing JSON draft responses, source-bounded
narrative rendering, automatic continuation pages and one-file signing fields.
Baseline: e15c5db / READY dpl_47tztcZ7rgRmvVYvdCdLUubDpBSz, independently
reconfirmed through the project connector during this continuation. No new
deployment, preview, migration, provider invitation, reminder or customer write.

## Implemented locally

- Relevant interview sections expose concise, labeled explanations. Water
  details remain conditional on choosing the water disclosure. Short names,
  websites and right numbers use one-line inputs; explanations use text areas.
- Saving preserves Unicode, literal markup, paragraph breaks, older hidden
  notes and boolean answers. An explicit cleared field clears that answer;
  server delivery-journal keys are never copied from browser state.
- Existing private-draft validation accepts the narrative keys, limits each
  explanation to 3,000 characters and rejects unsupported control characters.
  No database migration or new access requirement is introduced.
- Short answers fit measured source blanks; longer answers receive a visible
  continuation reference and are copied completely to additional pages.
  Continuations follow all official pages, keeping water pages at 5-6.
- Continuations repeat property/context and contain initials for the actual
  parties only. Seller-first recipient identity and simultaneous invitations
  remain unchanged; unsigned local specimens are not signing evidence.
- Corrected a real assembly defect: one merged PDF previously received two
  field arrays when water pages were included. It now receives one flattened
  field array including source and continuation pages. SignWell's create
  document contract defines one field array per file:
  https://developers.signwell.com/reference/createdocument.
- Render revision is included in the existing delivery fingerprint, preventing
  recovery of an older generated packet that ignored the same saved notes.
  This is NOT evidence that seller-review attestations bind to changed answers.
- Candidate worker v103 is local only; production remains v102.

## Verification

- 88 focused tests passed in 0.751s. Coverage includes real renderers, actual
  asynchronous send assembly with fictional mocks, all twelve party/water
  combinations, ordinary/long/Unicode/multipage notes, validation, actual-source
  UI save/reopen and PWA expectations. No external send was performed.
- Isolated browser fixture used actual interview render/save/load functions
  with fictional local storage only, no SDK, account or external connection.
  Main and water explanations survived save and reload exactly, including
  accented names, newline and literal <paint> & trim. Both 390px and 1280px
  document widths matched the viewport, with no horizontal overflow.
- Desktop and phone screenshots are local QA evidence, not production:
  /private/tmp/hof-disclosure-explanations-desktop-20261015.png and
  /private/tmp/hof-disclosure-explanations-mobile-20261015.png.
- Prepare-only helper scripts/qa/check_seller_disclosure_explanations.py made
  three fictional full-source specimens: one Seller (5 pages), two Sellers
  and two Buyers with water (6 pages), and Unicode overflow (7 pages).
  All six ordinary source pages and the one-Seller/Unicode continuations were
  visually reviewed. After the final heading keep-with-next change, specimens
  were regenerated and the final Unicode continuation rerendered and reviewed.
  Source PDFs remain unchanged and are not added to the repository.
- Temporary fixture tab was closed, viewport restored and local server stopped.
  Existing pending provider tabs and the real user offer were preserved.
- Frozen candidate full regression passed: 2,667 tests in 89.157s, one
  environment skip, process exit zero. The intentional negative fixture emits
  `ERROR: Invalid fixture PDF` after the successful suite summary; it is not a
  failed test. Standalone TXR signer geometry and patch whitespace also passed.

## Remaining correctness work - not a user approval gate

This is a tested local checkpoint, not a release or completed-provider pass.
Whole-form review exposed pre-existing defects outside the new narrative area:

1. Some main-form answer anchors are wrong: the Roof answer can land beside
   Walls/fences, and smoke-detector/repair choice marks intersect captions.
   Calibrate every affected scalar/choice against the exact supplied source.
2. Water property-address placement and second-page repetition need correction;
   source first-page party initials are absent from the existing builder.
3. Remaining scalar/choice coverage includes occupancy duration, roof details,
   well counts and wholly/partly flood choices. Narrative coverage alone is not
   complete form coverage.
4. Review integrity needs content-bound evidence. Updating a draft clears its
   attestation flag, but existing completed review links can currently restore
   approval by matching only party identity and attested time. Bind review
   completion to exact response/source/render revision with conditional writes;
   stale review must never authorize a changed packet. Do not substitute a
   timestamp-only check or confuse delivery fingerprinting with this repair.
5. After these fixes, perform integrated fictional completed-provider review
   using the established test workflow. No existing completed disclosure
   specimen was identified by the prior bounded inventory; do not reuse an
   unrelated form as evidence or duplicate invitations without checking.

The original supplied forms and existing agent access remain in scope. These
are implementation and verification tasks, not brokerage-seat/source-owner
requirements. Broader listing agreements, broker-admin onboarding and other
form matrix cases remain separate unfinished roadmap items.
