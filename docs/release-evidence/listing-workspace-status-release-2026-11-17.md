# Save listing workspace status through the authenticated API

The dashboard sends `update_listing_workspace_status` with the workspace
ID, selected status, and the previous `updated_at` to the existing
authenticated API. One update matches the verified agent ID, the
workspace ID, and that timestamp. A stale or unavailable workspace
returns HTTP 409 with refresh guidance. The API confirms the status
and new timestamp from the returned row before reporting success.
An unconfirmed save tells the agent to check the current status before
retrying. The browser retains a rejected choice, prevents duplicate
clicks, and ignores the outcome after an account change.

The production catalog confirms all four required columns, the five
supported statuses, service-role update access, and the existing
timestamp trigger. No migration is needed for status changes. The
November 17 production candidate starts from `4a1ff217` and uses shell
v200. Focused checks passed in both checkouts. Isolated PostgreSQL
verified the actual timestamp trigger and the owner and stale-version
filters. Offline Chrome at 390px and 1280px verified successful save,
repeat click, conflicting revision, and account change.

Duplicate-safe creation is a separate release dependency. Production
lacks `hof_listing_workspaces.client_request_id` and the owner/request
unique index from `20261029192322_listing_workspace_create_idempotency.sql`.
Creation code needs a coordinated migration and verification against
those exact capabilities. No live rows or migration changed in QA.
