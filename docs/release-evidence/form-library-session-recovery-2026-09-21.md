# Form-library session recovery — 2026-09-21

## Outcome

The authenticated form library now recovers once when a browser presents an
expired session, retries the catalog request with the refreshed session, and
continues sharing that single request across every visible form card.

If the refreshed session is also rejected, HomeOfferFlow stops sending the same
invalid token to the protected endpoint. The agent sees a direct instruction to
sign in again, and requests resume only after the authentication state changes.

## Evidence basis

- Vercel production observability showed no runtime errors in the preceding
  seven days.
- In the preceding 24 hours, 13 of 24 observed function responses were `401`
  responses from the approved-form catalog after Supabase rejected the browser
  session.
- The change targets that measured request cluster without adding a page,
  background job, external provider, database write, or recurring cost.

## Verification

- Runtime tests execute the shipped catalog loader and cover successful session
  refresh, one retry with the new token, a failed refresh, a rejected refreshed
  token, suppression of repeat requests, explicit cache clearing, account
  changes, simultaneous form cards, and late responses.
- Focused form-library, brokerage-source, and seller-disclosure coverage passes:
  41 tests.
- The complete local test suite passes: 2,375 tests.
- Production verification remains part of the single coordinated post-reset
  release; no preview deployment was created for this change.

## Expected impact

Agents with a refreshable session recover without reopening their work. A
definitively rejected token cannot continue producing repeated protected
function calls during that page session, reducing avoidable usage while keeping
the form-library privacy boundary intact.
