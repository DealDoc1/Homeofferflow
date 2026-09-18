# HomeOfferFlow lean development protocol

This is the default operating method for future HomeOfferFlow work. It keeps
quality high while reducing model context, repeated tests, Vercel builds and
duplicate QA.

## 1. One bounded workstream per task

Start a fresh task for each coherent batch, such as:

- simplify all four customer intake paths;
- correct a named group of related forms;
- improve checkout and receipt delivery; or
- prepare and verify one production release.

Do not use an open-ended implementation task as the permanent project record.
Use this repository's roadmap and release evidence instead of replaying old
conversation history.

Every batch begins with five facts:

1. intended user outcome;
2. exact surfaces or files in scope;
3. authoritative current production revision;
4. cost/release constraint; and
5. evidence required before the batch can be called complete.

Generate that compact starting context from the live repository instead of
copying an old conversation:

```bash
python3 scripts/build_lean_handoff.py \
  --outcome "One sentence describing the user result" \
  --scope "Named surfaces, files, or workflow" \
  --production-revision "Verified production commit or deployment" \
  --cost-constraint "Current deployment or paid-service boundary" \
  --evidence "Focused tests and any visual or live checks required"
```

The output is intentionally bounded to the current branch, commit, at most 20
changed paths and eight recent commits. It never reads task history, browser
state, environment variables, file contents, or customer data.

## 2. Model and reasoning budget

- Default: a cost-conscious medium-reasoning model, currently Sol Medium.
- Escalate temporarily only for a reproducible hard failure, security/payment
  boundary, database migration design, or consequential architecture choice.
- Return to the default model after the difficult decision is resolved.
- Prefer repository evidence and focused inspection over reconstructing prior
  decisions from a long conversation.

## 3. Evidence lives in the repository

Keep the roadmap factual: `implemented locally`, `locally tested`, `visually
reviewed`, `deployed`, and `production verified` are different states.

For each batch, record only:

- commit(s) and changed behavior;
- focused test command and result;
- visual/browser pages actually checked;
- external writes or sends, if any;
- release/deployment identity, if any; and
- remaining factual gaps.

Daily reports should be generated from Git history, test/release evidence and
current deployment state. They should not reread the entire task history.

## 4. Test pyramid

Run the smallest test that can disprove the current change:

1. **Edit loop:** targeted unit or component tests only.
2. **Batch checkpoint:** affected workflow tests and source synchronization.
3. **Release candidate:** the full regression suite once for the coordinated
   batch, after focused tests and visual review are already clean.
4. **Production:** canonical-domain smoke tests and only the live checks that
   cannot be proven locally.

Do not rerun the full suite after every form or copy edit. Rerun it only if the
release candidate changes after the full-suite result.

## 5. PDF and signing QA

- Inspect source geometry once and encode it in reusable layout constants.
- Test all supported transaction branches programmatically.
- Render a compact QA set containing changed pages only.
- Visually review one ordinary case, each materially different branch, a
  one-signer case, and one long/Unicode overflow case.
- Run completed-provider signing QA only when signing behavior or provider
  rendering changed. Never send real customer packets for routine layout QA.
- Preserve simultaneous invitations unless the transaction explicitly
  requires signing order.

## 6. Browser and UX QA

For a sitewide UX batch, exercise the four paths at one mobile and one desktop
viewport. Reuse a scripted path matrix and record only failures and final
results. Do not open or retain unrelated browser tabs.

Prioritize:

- clear industry-standard questions;
- conditional questions only when relevant;
- Google address completion wherever an address is entered;
- no internal/programming language in customer-facing copy;
- concise review screens; and
- one clean document package with minimal user effort.

## 7. Release and cost control

- Keep automatic Git deployments disabled.
- Build and verify locally while a batch is in progress.
- Confirm current Vercel headroom immediately before release.
- Use the existing prebuilt production workflow and one intentional deployment
  for the completed batch.
- Do not create routine previews or deploy documentation-only changes.
- Coordinate code and required database migrations in the same release; do not
  apply behavior-changing migrations alone.

## 8. Stop and checkpoint rules

Create a local commit when a coherent slice has focused tests and appropriate
visual evidence. Stop the batch when:

- its defined outcome is complete and evidenced;
- a factual external dependency prevents further safe progress; or
- the owner changes the priority or asks to defer the work.

Do not continue into a different workstream merely because time remains. Add
the next workstream to the roadmap and begin it in a fresh task when selected.

## 9. App-readiness discipline

Web work should keep business rules, document generation, authentication and
transaction state behind stable APIs. Keep the interview UI separate from
those services so a future mobile app can reuse the same workflows without
reimplementing legal-document or payment logic.
