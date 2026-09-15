# Saved-offer navigation under slow responses

Status: implemented and locally tested; not deployed or browser-verified.

## Customer outcome

The latest selected offer takes precedence when database responses arrive out
of order. Resume, Reuse Terms, and Duplicate & Edit share an opening-request
guard bound to the current draft and signed-in account. Starting a fresh draft,
choosing a different offer, or changing accounts prevents an obsolete request
from replacing the current interview or displaying a stale retry prompt.

Prepared-packet reopening retains its clean-copy behavior. If navigation
changes before copy insertion, that insertion is skipped. If insertion already
completed, the copy remains saved but does not open over the newer selection.
No existing record is deleted or changed by cancellation of an obsolete open.

Logging failures no longer turn successful Resume or Reuse Terms into errors.
A logging or offer-list-refresh failure after successful copy creation no
longer offers to repeat the creation. This is not a claim of exactly-once copy
creation after an ambiguous network failure during the insert itself.

## Local verification

- `node --test tests/offer_navigation_races.runtime.cjs`: 18 passed.
- Counterfactual against baseline `fa16a0d5`: 17 of the same tests failed; the
  same-account token-refresh control passed. Failures assert stale interview
  replacement, wrong-account continuation, unwanted copy insertion/opening,
  stale alerts, or false failures after successful UI work.
- Combined navigation, restoration-isolation, and autosave-switch tests passed
  before the final two logging-only regression cases were added. Both final
  logging cases and all previous checks are included in the full suite below.
- Full suite after the final code changes: 1,995 tests passed in 15.828 seconds.
- All 45 inline JavaScript blocks parsed successfully during review.
- `git diff --check`: passed.

Tests execute the actual application functions with deferred query promises
and UI doubles. They do not establish real-browser or live-database behavior.
Existing copy-metadata scrubbing and prepared-packet protection tests remain.
The source-based retry assertion now verifies the inherited opening request;
the existing runtime copy test loads the new request helper.

## Scope and release constraints

Supabase guidance informed the captured-account checks. Existing database
ownership filters, RLS, and the provider signing configuration are unchanged.
No customer record, email, signing packet, payment, or external setting was
modified. No additional dependency, migration, service, or recurring cost.

No GitHub publication, Vercel build, preview, or production deployment occurred.
The existing production spending and publication restrictions remain in force.
Live browser verification remains outstanding; prior browser-policy denial was
not bypassed. This local evidence supports the daily report, not a production
completion claim.
