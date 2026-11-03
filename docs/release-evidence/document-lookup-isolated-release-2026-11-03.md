# Saved-document lookup release candidate — November 3, 2026

## User outcome and exact scope

Find an existing prepared or signed client agreement before creating another.
The prepared forms list adds client/form/status search, Clear search with focus
recovery and explicit Load older documents. Signed records retain completed-PDF
access and their existing no-send rules. Searches remain within the signed-in
owner's loaded rows; this is not a cross-account or global client search.

Verified baseline: `66ce5eec3237f36f090f07eba110563ad71230a1`, READY production
`dpl_7xHmnYgoaxcHzr47gYtTjEump9Rt`. This candidate isolates roadmap checkpoints
`ca904021` and `653080a6` on that exact baseline. Product files are only
`api/admin-dashboard.py`, `index.html` and `service-worker.js` (shell v132).
Tests and this evidence complete the seven-file candidate. No source PDFs,
renderers, signing fields, provider requests, recipients, send/retry workflow,
IABS handling, representation-package behavior, schema or billing changes.

The production list predates roadmap package/listing metadata. Those additions
were explicitly excluded, rather than importing their form dependencies. The
list/page callbacks include the viewer identity/epoch checks they need, while
all existing rendering and signing functions stay at the released version.

## API contract and safeguards

The existing authenticated `scope=standalone_agreements` endpoint keeps its
agreements and signing flags and adds pagination metadata. A default request
still returns at most 100 rows; one extra row determines whether a next page
exists, without an aggregate count. Every page has a validated UUID owner
filter, a bounded decimal offset, and updated_at/ID descending ordering.
Private agreement JSON is removed after deriving the existing safe summaries.
Malformed input fails before reading; service failures return generic 503.
No browser-supplied owner or write action is accepted.

Each Load older action requests one page. Results deduplicate by ID, retain the
query, and focus the first new matching row. Failed pages retain the current
list and cursor; duplicate clicks cannot issue overlapping page loads. Older
replies cannot replace a refreshed list or another viewer's card. Refreshing
starts with the latest page. Offset paging is a live view, not an atomic snapshot;
concurrent updates can move records. The UI describes searching listed records,
not a complete remote archive scan. No query is persisted in browser storage.

## Validation and user experience

- 97 focused tests passed on the isolated candidate: history API, real renderer/
  event-handler search and paging, signature recovery UI, agent dashboard,
  library feedback and standalone agreements.
- Full pinned-runtime regression: **2,976 tests passed, 23 skipped**, 95.236s.
  Existing txr1101-runtime interpreter and dependencies; no local installation.
- Runtime checks cover actual authenticated loader offsets/default request,
  multi-term/Unicode/form-code matching, escaped text, signed no-send/download,
  100-row pages, duplicate IDs, retry, non-advancing page rejection, rapid double
  clicks, refreshed-list races, focus, empty/failing lists and account switching.
- API checks cover lookahead/output bounds, owner filter, timestamp tie ordering,
  private-JSON removal without input mutation, invalid owner/offset, valid next
  offsets near bounds, malformed store results, actual GET authentication and
  error sanitation. No real database or signing service was used for these tests.
- Supabase branch preflight passes (123 migration files). No migration included.
  Whitespace passes; normal preflight identifies no packet/form source/map change.
- Exact candidate UI reviewed with fictional localhost data and repository styles
  at 390x844 and 1280x800. Search, initially absent older clients, failed older
  load, retry, new-row focus, signed/draft controls, clear focus and no-more state
  were checked. Temporary browser viewport/tabs/server were cleaned up.

## Release boundary

Local implementation, focused/full tests and visual review are complete.
Exact-head PR CI remains required. Use only the existing prebuilt production
workflow after author/tree checks and its live target/schema/cost reserve gates.
Automatic Git deployments remain disabled; no preview or documentation-only
release. The owner retains standing authority for verified cost-checked releases.

This is list navigation and an additive read API. It changes no packet creation,
PDF, signing map or provider rendering, so no new provider signing specimen is
needed under the lean protocol. This evidence does not clear other roadmap form
or signing QA. No customer packet, message, invitation, credential, live data
write or charge occurred during preparation. Production deployment and canonical
verification are not yet claimed.
