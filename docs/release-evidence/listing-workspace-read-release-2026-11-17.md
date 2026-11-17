# Listing workspace reads for web and future mobile clients

The dashboard list, disclosure picker, and saved listing handoff now
share `GET /api/admin-dashboard?scope=agent_listing_workspaces`. Send
the normal verified session bearer token. The optional `workspace_id`
limits the search to one saved record, and `limit` defaults to 20 and
is bounded at 50. The response is `{"workspaces":[...]}`, newest first.
A missing or foreign listing returns an empty list. An invalid ID or
limit returns HTTP 400, a missing session returns 401, and a storage
failure returns 503. The route is private and uses the existing no-store
response header.

The server derives ownership from the session and reads only the fields
used by the listing and disclosure views. Browser reads expire after
15 seconds. Late dashboard reads and disclosure results are ignored
after account changes. Listing writes and signing flows are outside
this change.

The release candidate starts from `9a765e176` and advances the installed
shell to v199. A read-only production catalog query confirmed all eight
columns, RLS, the authenticated owner SELECT policy, and service-role
SELECT privilege. No rows were read and no migration was needed.

Focused tests covered owner filtering, rejected sessions and IDs, limits,
storage errors, listing dashboard integration, and disclosure UI. Offline
Chrome at 390px and 1280px verified listing selection, disclosure prefill,
failure recovery, and late response suppression with fictional data.
