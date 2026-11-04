# Dark form readability — November 4, 2026

Owner request: make My Offers search text white and review similar dark-on-dark
text elsewhere. Baseline production ab4037d8a47f5ca98500d6d35c711f189734fef5,
shell v134. Scope: shared dark form CSS, calculator placeholder CSS and shell cache.
No JavaScript, API, schema, PDF, signing or billing changes.

The shared rule gave every input/select/textarea a dark background without a
text color. Bare search, sort and several auxiliary fields used native black.
Set white text and caret with native dark color-scheme. Replace the interview's
20%-white placeholders with existing gray-light at full opacity, and give bare
placeholders the same readable default. Existing component colors still take
precedence; no blanket important color override. Production shell advances to
v135; the roadmap shell independently advances to v219.

## Focused verification and review

20 existing offer search/export/history/signing-recovery tests passed. No new
CSS-string assertion or implementation-mirroring test was added for this styling
change. The runtime search regression still proves uninterrupted typing and
cursor preservation.

Browser review used script-free copies of actual public markup/styles plus a
fictional control specimen. Active styles were extracted after removing scripts,
so inactive print-document template styles were excluded. No live customer
records, form submissions or network provider calls were used.

The actual shell's 192 enabled textual/select controls were computed before and
after the change. Before: four bare static controls used dark text (missing form
name, seller website confirmation, partner model and partner confirmation), and
115 placeholders were below the 4.5 contrast screening threshold. The dynamic
My Offers search and sort reproduce the same black-text default in the specimen.
After: none of those 192 controls are below the screening threshold. Minimum
computed text ratio 14.75; minimum placeholder ratio 7.63. This screen composites
CSS background colors and alpha through ancestors; decorative background images
and native popup pixels are not a full-site accessibility certification.

The fictional specimen was visually reviewed at desktop and 390x844: search,
selected sort, address, client, email, notes, financing, date, disabled control,
prepared-document search and library fields. Search/sort are white; placeholders
remain distinct and legible. The public buyer/agent/seller/investor first screens
were reviewed at both sizes. Their existing light text was readable. Public
partner, directory and brokerage pages were also checked for form color defaults;
directory's two controls are white and brokerage email is existing near-white.
The other five landing pages have no static textual controls. Their later
shared app forms are included in the shell CSS review, not claimed as complete
end-to-end transaction tests.

Private evidence: /private/tmp/hof-form-contrast-audit-2026-11-04.json,
/private/tmp/hof-form-contrast-desktop-2026-11-04.jpg and
/private/tmp/hof-form-contrast-mobile-2026-11-04.jpg. Temporary viewport reset
and QA tab closed. Full frozen candidate regression and exact-head CI precede
release. The existing intentional workflow must repeat current project/schema/
frequency/spend checks before one prebuilt production deployment. Automatic Git
deployments remain disabled; no previews or documentation-only deployment.

Signing transport work is preserved separately on
codex/buyer-qa-transport-release-2026-11-04 / 7ad5a95e / PR #1373 and is not part
of this candidate. Its 100 focused tests passed. Its full local run reached
3,012 tests but one source case lacked HOF_BUYER_QA_IABS_SHA256 in the command;
this is an identified test environment setup issue, not a passed full run or a
provider finding. No new provider attempt or signing release occurred.


## Complete tracked form-page inventory

A tracked-file inventory (scripts removed before parsing) identifies all six
pages with static non-checkbox/radio text controls: index (192), directory (2),
brokerage enrollment (1), internal field mapper (17), seller review (2), seller
net-proceeds calculator (7): 221 controls total. This supplements the seven
public-page and four-path first-screen review, plus dynamic search/sort specimen.
Field mapper and seller review have readable existing text (minimum screening
ratios 12.5 and 21). No uploads, debug PDF filling or submissions were performed.

The calculator's seven native gray placeholders screened at 4.11. Give them the
page's existing muted light text at full opacity. The corrected minimum is
10.69 (typed text stays 18.96). Desktop/390x844 calculator fields were visually
reviewed. Existing calculator calculations and privacy contract are unchanged.
Final focused run: 27 tests including seven existing calculator tests. The first
frozen shared-CSS candidate's full regression passed 3,002 tests, 26 skipped,
115.017 seconds. The subsequent calculator-only CSS rule has its focused tests;
exact-head CI and the production workflow must test the final complete tree.
No redundant local full rerun for this one CSS rule. Final calculator proof:
/private/tmp/hof-calculator-contrast-mobile-2026-11-04.jpg and
/private/tmp/hof-calculator-contrast-after-2026-11-04.json.
