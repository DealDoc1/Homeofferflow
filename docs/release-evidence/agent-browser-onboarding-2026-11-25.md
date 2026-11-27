# Agent browser onboarding

The agent landing page now names its returning-agent link Open agent workspace
and explains browser access using the email sign-in link. Optional collapsed
instructions describe adding a HomeOfferFlow phone shortcut. The link retains
its existing destination and does not select a transaction. On phones the
header actions stack to keep the link labels readable. The installed shell
advances from v237 to v238 for the eventual release.

The 62 existing agent landing funnel tests pass after updating the existing
link-label expectation. Both offline shell runtime checks pass. Release
preflight and whitespace pass. Offline Chrome at 390px and 1280px verified
workspace destination, keyboard expansion of the install help and no horizontal
overflow. Both sizes were visually inspected, and the phone header adjusted
and inspected again. Requests were blocked during browser checks.

This is a local queued checkpoint on production base 6e6ae51ec. Bundle it with
the next verified runtime release, then rerun release regression and current
cost checks. No production deployment or external message was made.
