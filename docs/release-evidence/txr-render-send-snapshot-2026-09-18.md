# TXR render-to-send snapshot - September 18, 2026

**Local implementation and offline integration tests only. Not deployed.**

## Finding and change

Standalone signing previously queried its draft and approved source, downloaded
the source, and then called the public preview helper, which repeated all three
reads. This meant the PDF could be rendered from a newer draft than the recipient
list and field map. The existing version-checked checkpoint already prevented
an invitation in the simulated concurrent-edit case; this was not evidence that
the older implementation emailed a mixed-version packet.

Both preview and send now use one private rendering helper after their existing
owner-scoped draft lookup. Sending supplies the same server-loaded draft used
for its recipient list, signing-field map and version-checked save. The shared
helper retains the approved-source revision check, private download and rendering
context fingerprint. The browser cannot supply a draft snapshot to this helper.

This removes one agreement lookup, one source lookup and one source-PDF download
per preparation attempt. It should reduce unnecessary waiting and resource use;
no live latency measurement or dollar savings are claimed. No new user-facing
approval, brokerage seat, account, subscription or workflow step was introduced.

## Offline verification

- 34 focused tests passed, including the new actual-render/actual-dispatch/
  actual-delivery-adapter tests and existing recovery/recipient checks.
- TXR-1501 and TXR-1507 run through both broker and associate roles with one and
  two clients. The new tests use synthetic blank source pages and stateful HTTP
  doubles; no copyrighted source or customer PDF is committed.
- The exact base64 PDF submitted to the simulated provider is parsed. Its party
  names, page count and field-to-page assignments are checked. Long-form
  continuation initials reach every actual added page for all signer variants.
- A concurrent edit changes the saved version and client name during source
  download: the PDF remains based on the original snapshot and the existing
  conditional checkpoint blocks sending. The newer saved answer is untouched.
- Wrong source revision, inaccessible source, non-PDF response and unavailable
  owned draft stop before provider creation. Existing tests retain rejection of
  unconfirmed recipients and unsafe untracked retries.
- Running two new regression methods against the prior committed implementation
  produced nine failures: eight duplicate-download cases plus a mixed-snapshot
  private draft. The current implementation passes these tests.
- Full discovery: 2,199 tests in 49.813 seconds; 2,197 pass and the same two
  approved signing-map reference comparisons fail. No new failure was found.
  The reference files were not regenerated to conceal pending placement QA.
  Log: `/private/tmp/hof-txr-render-send-snapshot-suite.log`.

## Security and limits

The Supabase skill prompted review of the current changelog and API security
guidance. No relevant breaking change applies to this internal refactor. Both
entry points retain their owner-scoped lookup; no service-role credential is
exposed, and no schema, grants, RLS policy, auth logic or SQL write contract was
changed. Conditional persistence was exercised using stateful local doubles,
not a live database test. A live deployment/integration claim remains unsupported.

This verifies consistency within a send attempt, not a cryptographic binding
to the last PDF the user viewed earlier. It is not new visual or completed-
SignWell QA; no coordinates, rendered content or signed customer PDFs changed.

No push, Vercel build/deployment, customer email, live provider request, database
mutation, paid test or new resource occurred. Previously outstanding signing-map
reference comparisons and completed-provider QA remain outstanding.

References: [Supabase changelog](https://supabase.com/changelog) and
[API security guidance](https://supabase.com/docs/guides/api/securing-your-api).
