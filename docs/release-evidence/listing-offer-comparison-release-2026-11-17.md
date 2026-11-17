# Keep listing offer comparisons private and conflict-safe

The listing comparison worksheet uses the authenticated dashboard API
to load, add, mark, and remove private comparisons. The server checks
ownership of the listing workspace and scopes comparisons to the
verified agent. Status changes and removals carry the last-seen
`updated_at` value. A conflict keeps the newer record and asks the
agent to refresh. An uncertain save keeps the form contents and asks
the agent to check for a saved comparison before retrying. Late
responses cannot replace another account's comparison view.

The browser uses the same list and comparison fields as before and
still asks before removing a comparison. Progress, confirmation and
conflict messages are visible. The API supports the existing statuses
and values and is reusable by mobile clients.

The isolated candidate starts from `c7aa1542` and serves shell v202.
The production catalog confirmed the existing comparison table, RLS,
and service privileges for reads and writes. No migration, signing
provider request, or live comparison write was needed in QA.
Focused API and workspace tests passed. Offline Chrome at 390px and
1280px verified creating a fictional comparison, updating its status,
rejecting stale removal, confirming removal and isolating account changes.
