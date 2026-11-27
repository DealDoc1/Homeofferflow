# Agent search and browser onboarding release candidate

## Outcome and scope

Base is protected production `6d66e3e1cc600e5d26f9b60ebeb498851bbb2b60`,
READY at `dpl_35rWBKbfuZZncycujL3gU6Nh9sPv`. This isolated candidate includes
only bounded canonical co-buyer names in the authenticated offer projection,
web search matching for those names, the previously reviewed agent browser
entry/phone-shortcut guidance, corresponding tests and shell v239.

No PDF renderer, signer map, invitation path, API mutation, billing terms,
partner placement or database migration changes. Native app store release,
custom document packages and uploaded-contract Gemini review remain separate.
Automatic Git deployment remains disabled in vercel.json.

## Local and user-experience verification

81 focused tests passed using the pinned project Python:

```sh
python -m unittest tests.test_agent_offer_history_api \
  tests.test_agent_offer_detail_api tests.test_offer_workspace_search \
  tests.test_offer_workspace_export tests.test_agent_landing_funnel -q
```

API cases cover current/legacy source precedence, malformed/missing names,
200-character bounds, owner scoping and secondary-contact exclusion. The actual
workspace script's rendered-DOM tests cover normalized co-buyer queries,
combined property terms, empty results, clearing and retained input focus.
The existing production search implementation is preserved except for adding
co-buyer fields. No markup/layout change was needed for search.

The agent landing page is byte-identical to the candidate visually reviewed
November 25 at 390px and 1280px. That review verified keyboard expansion,
workspace destination and phone width. See agent-browser-onboarding-2026-11-25.md.
No new live browser observation is claimed while the owner has the Expo handoff.

Full candidate regression passed: 3,245 tests in 115.637 seconds, with 29 skips.
Command: python -m unittest discover -s tests -q.

## Schema, project and cost checks

Read-only production catalog inspection confirmed the existing buyer2_name
column. Core, seller-disclosure, purchase-disclosure and rental-source readiness
RPCs all returned ready=true, missing=[]. The listing-workspace check is true
and core reports sale_listing_ready=true. No migration is required or applied.

Authenticated Vercel inspection confirmed the existing homeofferflow project
and team. Its latest 20 deployment records extend before the current 24-hour
window; one deployment falls within that window, below the conservative limit
of 12. Current billing-cycle usage was read for November 22 through 27, 2026.
Managed infrastructure totals $0.006127445046666666, excluding fixed plan/add-on
fees, against the existing $20 credit and $3 reserve. The intentional workflow
must repeat its schema, project, capacity/spend and prebuilt runtime gates.

This evidence describes the candidate. PR/CI, merge, release run, deployment and
canonical verification must be recorded only after their actual results.
