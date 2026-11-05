# My Offers word and name matching — November 4, 2026

Outcome: locate a loaded offer using words from its buyer, property, email or
status in any order, with accent/apostrophe normalization. Baseline production
bd787121894242089c4f81bbbb42d118edd91f09, shell v135. Scope: existing client
matcher, actual workspace runtime regression and future shell-cache version.
No API, schema, document, billing or network request change. Search still covers
loaded offers; this does not claim a server-wide or unloaded-history search.

Evidence: the prior exact-phrase includes check rejects Alex Maple even though
Alex Lee's offer is at 123 Maple Lane. A new actual-script regression failed
against that implementation before the change. Prepared-document search already
uses word-by-word accent folding (see prepared-agreement-search-2026-11-03.md).
My Offers now normalizes NFKD/Latin combining accents and straight/curly
apostrophes for matching only, lowercases, and requires every query word in the
same offer's existing search fields. Saved/displayed names and addresses stay
unchanged. Cross-offer words never combine. The existing shared predicate also
keeps visible-card and CSV selection consistent.

30 focused tests pass across offer_workspace_search, offer_workspace_export,
offer_workspace_retry, offer_workspace_signing_recovery, agent_offer_history_api
and offer_detail_accessibility. The complete actual workspace script is executed
in Node. New cases cover buyer-plus-address words, reverse order, repeated spaces,
case, accented/combining names and email, straight/curly apostrophes, non-Latin
names, cross-offer negatives and whitespace-only clear. Existing typing/caret/
input identity/persistence regressions remain. No new dependency or duplicated
production matcher in tests.

The verification workflow follows typing -> existing in-memory loaded offers ->
shared predicate -> cards/count/clear. There is no new API/server/data boundary;
the history API's existing owner/paging tests remain green. Browser review uses
the actual workspace script and active styles with four fictional records.
Alex Maple and Maria Clair each show exactly one correct offer. Desktop and
390x844 views retain white search/sort text and readable results; focus remains
on the same input. Phone edit/backspace keeps the matching card; Alex Clair
shows none because its words belong to separate offers; Escape restores four.
Browser error log is empty. Initial viewport resize needed a fresh layout
observation before its screenshot; the settled 390px layout is the reviewed one.

Private proof: /private/tmp/hof-offer-word-match-desktop-2026-11-04.jpg and
/private/tmp/hof-offer-word-match-mobile-2026-11-04.jpg. Temporary QA tab closed,
viewport reset and local server stopped. No customer data, provider request or
external message. Roadmap shell v220 reserves refresh for this local UI work;
an isolated production release must advance the current production cache once.

Implemented, focused-tested and browser-reviewed locally. Not deployed or
production-verified. Full frozen-candidate/CI/project/schema/cost checks remain
for the next intentional production batch. No preview or documentation-only
deployment. Automatic Git deployments remain disabled; user mobile/ untouched.


## Isolated release candidate

Candidate branch: codex/offer-word-match-release-2026-11-04. Baseline is still
verified production/main bd787121894242089c4f81bbbb42d118edd91f09. Only the
matcher patch, actual runtime regression and evidence are copied from roadmap
checkpoint 4018d0ba; isolated shell v135 advances to v136. Protected signing
transport and both preserved QA reservations remain untouched. Existing APIs,
interviews, partner placements, PDFs and customer records are unchanged.
The exact helper and regression match the previously browser-reviewed source.
Full regression, exact-head CI and existing live release checks remain required.

The roadmap's 30-case run includes seven separate local history-API cases that
are not present in this production baseline. The first isolated focused command
therefore stopped on that unavailable module before launching a full run.
Use the five present workspace/detail suites for the 23-case isolated focus;
do not copy unrelated API code/tests into this release. The matcher itself and
its full actual-script regression pass in both checkouts. The later full/CI
results must come from this isolated production tree.
