# Accurate acquisition activity units in Admin

## Outcome, source and scope

The authenticated canonical Admin screen showed 120% overall and 600% by
channel as homebuyer/agent conversion. The backend divides aggregate action
events by aggregate landing-view events. Repeat actions, direct workspace
entries and independently observed stages mean these are event ratios rather
than matched visitor cohorts. A channel with starts but no landing view was
previously omitted from the displayed rate list.

This bounded change starts at verified production
aeda19c33dffea3add04b50994ca826f4e1e7963 and changes only the two affected
Admin cards, their formatting helpers/tests and the public-shell cache marker.
The existing aggregate API fields, arithmetic and historical events remain
intact, preserving consumers and privacy. No new visitor identifiers, database
change, paid service or customer-facing workflow is introduced. Automatic Git
deployments stay disabled; no preview or standalone documentation deployment.

## Behavior

The cards report actions per 100 landing views and label channel activity
explicitly. Values above 100 remain visible with their correct units. The
same units apply to the cards' overall landing ratios. Channels with actions
but no view now show no landing views recorded instead of disappearing or
implying a measured zero conversion. A concise explanation names repeat
actions and direct workspace entries. Channel labels remain HTML-escaped.
Other independently defined funnels and campaign metrics retain their existing
contracts and are outside this slice.

## Verification

All five new executable helper/actual-card regressions failed before the fix
and passed after it. They exercise repeated starts, absent/invalid denominators,
channels without views, label escaping, and actual homebuyer/agent template
rendering from index.html with fictional metrics. Legacy supplied percentage
fields cannot make the changed cards claim 600% conversion.

74 focused Python tests passed, including the wrapper that runs all five new
Node checks. The three existing channel-summary Node tests also passed:

```sh
python -m unittest tests.test_homebuyer_landing_funnel \
  tests.test_agent_landing_funnel tests.test_admin_funnel_activity_runtime -q
node --test tests/admin_channel_summary.runtime.cjs \
  tests/admin_funnel_activity.runtime.cjs
```

Chrome review used the actual changed card templates and existing CSS with
fictional metrics only, served on localhost. Screenshots were visually reviewed
at measured CSS content widths of 390 and 1280 pixels. Text/contrast/wrapping
passed, the explanation rendered, and document scrollWidth equaled innerWidth
at both widths. The temporary viewport was reset and review tab closed.
An initial harness omitted UTF-8 metadata; that harness-only issue was corrected
before final review. No product encoding change was needed.

git diff --check passed. No live customer packet, signing action, provider
request, outreach or deployment occurred. This is locally implemented/tested
and visually reviewed; deployment and canonical verification are pending.
Full regression and fresh release/cost gates apply to the final batched release
candidate, not to each local card edit.
