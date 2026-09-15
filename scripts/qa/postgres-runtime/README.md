# Local PostgreSQL concurrency QA

This optional **macOS arm64** test runtime is not an application dependency.
The entire `scripts/` directory is excluded from Vercel releases. Packages are
pinned and the lockfile records their integrity hashes. No Docker, hosted
database, account credential, paid service, or production connection is used.

From this directory:

```sh
npm ci --ignore-scripts --no-audit --no-fund
cd node_modules/@embedded-postgres/darwin-arm64
node scripts/hydrate-symlinks.js
```

The reviewed package hook only recreates the runtime's bundled relative library
symlinks. The native package and upstream build are documented in
[embedded-postgres](https://github.com/leinelissen/embedded-postgres).

Then, from the repository root:

```sh
HOF_PG_QA_MODULES="$PWD/scripts/qa/postgres-runtime/node_modules" node scripts/qa/check_packet_usage_concurrency.cjs
```

Alternatively install these locked dependencies in a temporary directory and
point `HOF_PG_QA_MODULES` to its `node_modules`, as used in release verification.
On a restricted execution host, PostgreSQL may need permission to create its
local shared-memory segment. This is not production database authorization.

## Safety and scope

The runner does not accept a connection URL. It creates a new private directory
under `/private/tmp/hof-pg-usage-*`, initializes an empty PostgreSQL 17 cluster,
disables TCP listening, and connects only through that directory's private Unix
socket. All rows are synthetic. Eight workers have distinct PostgreSQL backend
process IDs; actual lock waits are observed before the coordinator commits.

The runner applies the real packet-usage migration to isolated fixture tables.
It tests last-slot contention, duplicate completion, same-packet contention,
stale-worker fencing, atomic summary reads, independent-account progress,
release/replacement ordering, disconnect rollback, billing-status changes,
and denial of client-role RPC calls.

`finally` closes clients and stops the cluster; output confirms the PID file is
gone. The synthetic fixture directory is retained for diagnosis, not deleted.
This is real PostgreSQL concurrency QA, but **not** a full Supabase/PostgREST,
production-schema, provider-delivery, or live-inbox test.
