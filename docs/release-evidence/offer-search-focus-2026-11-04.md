# My Offers search focus repair — November 4, 2026

Outcome: agents can type and edit a complete search without clicking back into
My Offers after every character. Scope: index.html agent workspace rendering,
service-worker shell cache and focused runtime regression. Baseline production:
8dd7ab09914225ba01f66b80b8a050521d45e48f, shell v133. No API, schema, PDF,
signing, billing, authentication or customer document changes.

The owner-reported defect was reproduced in the signed-in canonical workspace:
a single character filtered the results but moved focus to the web area.
The original search setter rebuilt myOffersList and detached its input.
Search now updates only the card list and live result summary. The input,
selection, composition, sort/status controls and native keyboard remain intact.
A shared pure rendering helper keeps full renders and incremental search results
consistent. Existing state persistence, matching, filters and sorting remain.

20 focused tests passed across offer_workspace_search, offer_workspace_export,
offer_workspace_retry and offer_workspace_signing_recovery. The Node regression
executes the actual complete workspace script with fictional offers and verifies
input identity/focus/caret, uninterrupted prefixes, middle edits, Unicode query,
empty results, backspace, clear, programmatic updates and persisted state.
Whole-parent writes fail the regression, reproducing the old defect.

The actual script with repository styles and fictional offers was reviewed in
browser at the default desktop viewport and 390x844. Sequential native typing,
mid-word arrow/backspace edits, no results, Escape clear and a second search
preserve focus and update results/count correctly. The temporary tab was closed
and viewport reset. Private screenshots: /private/tmp/hof-offer-search-mobile-2026-11-04.jpg
and /private/tmp/hof-offer-search-desktop-2026-11-04.jpg. No real offer was changed
or sent; the live diagnostic search was cleared back to its original empty view.

Release constraint: automatic Git deployments remain disabled. No preview.
Use one intentional existing prebuilt production workflow after exact-head CI,
full regression, release preflight and current schema/project/frequency/cost
gates. Latest refreshed usage this session: $0.02 of $20 credit, $19.98 remaining
before the required $3 reserve; usage may lag an hour. The workflow must repeat
its checks immediately before deployment. Isolated release shell v134; roadmap
checkout has its own unreleased shell version. Unrelated signing work remains
preserved on its separate committed branch.

This checkpoint records implemented, focused-tested and browser-reviewed work.
Deployment and production verification require separate observed evidence.
