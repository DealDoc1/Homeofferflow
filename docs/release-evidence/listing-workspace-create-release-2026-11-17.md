# Retry listing workspace creation safely

The dashboard sends a request UUID to the authenticated
`create_listing_workspace` action. Retrying unchanged details reuses
that UUID. The API returns the matching saved workspace if the first
request committed before the connection failed. The server checks
ownership and validated details. Requests with different details get
a new UUID, and legacy API callers may omit the key. The server
assigns the owner, starting status, and eligible brokerage. Retrying
preserves the entered details. The pending UUID and details are held
in page memory for the active account, and late responses cannot
clear a different account's form.

The candidate on `a69aa584` includes the existing timestamped migration
`20261029192322_listing_workspace_create_idempotency.sql`, now with
a service-role-only release check for the column and the exact valid
partial unique index. The production release script fails closed if
the capability is absent. The production catalog reported the column,
index and check absent before release. Personal listing access is
already present. The migration and application are one release unit.

Isolated PostgreSQL verified the exact migration, duplicate rejection
for the same owner, reuse by different owners, legacy null-key inserts,
restricted access to the gate, and rejection of a wrong index.
Focused API and schema test suites passed in both checkouts.
Offline Chrome at 390px and 1280px verified a lost response, same-key
retry, reuse of the saved row, and an account switch with fictional data.
The isolated application uses shell v201. No signing behavior is involved.
