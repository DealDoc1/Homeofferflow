# Agent form-coverage request path evidence — 2026-07-31

## Change

Commit `54ffd8f` adds a dedicated **Request a missing form** action to the
agent launch-scope card. It opens the existing authenticated feedback workflow
with `missing_addendum` selected and asks for the form/workflow, transaction
role, and intended behavior without collecting confidential client details.

This gives agents a clear route for unsupported buyer, seller, landlord,
tenant, listing, and representation workflows while the form catalog is built
through source and QA gates.

## Verification

- `tests/test_agent_launch_scope.py` verifies the request action, category, and
  privacy guidance.
- Full repository suite: 363 passed in the current verified main baseline.
- No legal-form source, field mapping, signer plan, or production PDF workflow
  was changed.

## Release status

Bundled for the next intentional Vercel release under the Hobby deployment
policy. Unsupported forms remain unavailable until their separate source,
mapping, signer, rendered QA, and release gates pass.
