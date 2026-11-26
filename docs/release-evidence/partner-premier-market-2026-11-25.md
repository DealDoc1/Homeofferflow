# Preserve the selected workflow Premier under market filtering

The production workflow query applies its market filter before choosing the
existing top Premier. A later Premier can therefore become eligible when the
selected Premier is outside that market. This isolated release ports the existing
roadmap fix from d060183a5 onto production be97061aa.

The workflow now chooses the same top Premier before checking market relevance.
A nonmatching market returns an empty suggestion list. Directory market filtering
remains scoped to directory queries. Selection order and response shape are
preserved. No partner record, category, pricing or placement entitlement changes.

Forty-eight Python checks passed across partner lead selection, public profiles
and directory impressions. Forty-one UI runtime checks passed across roofing,
insurance and public profiles, covering empty results, failure/retry, hidden
steps, rendered partner cards and bounded impression/click data. No UI markup
or styling changes. The empty-state behavior was reviewed through those runtime
checks. Whitespace and release preflight passed against be97061aa.

This candidate is local. Full candidate regression, GitHub CI and the intentional
production workflow remain required before deployment.
