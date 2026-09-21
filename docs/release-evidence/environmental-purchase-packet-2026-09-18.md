# Environmental review in the purchase packet - September 18, 2026

## Status

Local candidate only. Not pushed, deployed, or sent to SignWell. No customer
agreement changed. Completed-provider signature artwork and live authenticated
source retrieval remain unverified. Existing release/cost restrictions remain.

## User experience and packet behavior

- Purchase interview asks whether environmental review rights are needed.
  Only a Yes shows the three source-form review choices and the agreed
  termination period. Neither the rights nor the period is defaulted.
- Reuses property and buyer details and the existing shared seller contacts.
  No brokerage seat, new account, or new per-agent approval requirement added.
- Browser and server both validate selected rights, whole days (1-999), and
  distinct, complete signer identities. Deselecting clears submitted terms;
  draft restoration clears another offer's old checkbox values.
- Includes TXR-1917 in the same PDF after hydrostatic/mineral addenda and before
  uploads, with the correct Paragraph 22 checkbox. Real page counts include
  continuation pages, and seller recipient IDs remain 3/4 throughout.
- The signing request still uses simultaneous invitations. Sellers sign the
  addendum, not the core purchase contract unless an existing seller-execution
  workflow independently calls for it. Review and invitation copy describe
  this distinction. No actual invitation was submitted during this work.
- Summary says "Review rights," not "Reports included": no environmental
  assessment is performed and no third-party report is ordered.

## Source and placement

Privately supplied TXR-1917 / TREC 28-2, 12-05-11, one static US Letter page,
zero canonical fields and zero widgets. Source SHA-256:
`99a3df4d6d8142dabc6ec8c88a11415c937bc85d3c29e52127ec942059dc5742`.
No source PDF or client data is committed.

The previous signature boxes crossed the printed horizontal bounds and ended
slightly below their rules. Buyer boxes now span PDF x=55.5..286.5, seller
boxes x=325.5..556.5, inside source rules x=54..288 and 324..558. First-row
bottom is 531 versus source rule 532.38; second-row bottom is 601.5 versus
602.88. Both leave a 1.38-point gap above the printed line. These are requested
field bounds, not proof of the size of completed SignWell artwork.

Address, days, and review-only names use measured blanks with a minimum
seven-point font. Long answers receive a lossless labeled continuation and
initials for every signer. Signing versions suppress draft names in signature
spaces. Render revision: `txr-1917-2026-09-18-source-blanks-v2`; standalone map
revision: `txr-1917-2026-09-18-execution-candidate-v2`.

## Verification evidence

- 54 focused Python test methods passed, including the JavaScript runtime
  wrapper. The interview runtime separately passed all 20 checks.
- Full discovery: **2,151 tests; 2,149 passed; 2 failed** in 38.481 seconds.
  Failures are the existing approved-map comparison methods; this candidate
  adds TXR-1917 changes to their drift. No approved baseline was overwritten
  to make the suite green. Log: `/private/tmp/hof-environmental-packet-suite.log`.
- Backend tests cover all one/two-buyer and one/two-seller combinations,
  eight checkbox subsets at renderer level, source mismatch rejection,
  malformed choices, all-addenda/upload ordering, continuation recipient IDs,
  deselection, and one-file simultaneous provider payload using mocks.
- An isolated localhost bridge used actual interview markup, collectors,
  validators, and PDF/field builders with synthetic data. Browser results:
  missing choices/days/email prevented generation; environmental alone made
  13 pages; environmental + minerals + hydrostatic made 15, with hydrostatic
  fields on page 13, mineral fields on 14, and environmental fields on 15;
  deselecting environmental made 14 pages and
  removed its terms and all TXR-1917 fields. Five hydrostatic widgets retained
  matching canonical values, parents, and appearance streams.
- Page loaded, controls rendered, no error overlay. Browser log later contained
  "Could not establish connection. Receiving end does not exist." Packet
  generation succeeded; no zero-console-error claim is made. One temporary
  browser tab was closed and the local server stopped after verification.
- PDF skill visual checks: generated TXR-1917, contract Paragraph 22, and both
  pages of a long-address/two-buyer/two-seller field-outline specimen. Address,
  all three X marks, days, signature bounds, continuation text and initials
  clear printed content. Specimens remain private under `tmp/pdfs/` and are
  unsigned; field outlines are not provider-completed signatures.

## Source access and remaining checks

Reuses the existing server-only private-source lookup. Tests simulate the
approved source row and authenticated storage response; no production query,
policy change, schema migration, or new service was made. The Supabase skill
security review confirmed credentials and source bytes remain server-side.
Official private-download documentation was checked:
https://supabase.com/docs/guides/storage/serving/downloads
Live source access is not proven by the mocked response.

Remaining release work: live authenticated source retrieval, controlled
completed-provider placement QA, and an authorized production release with
canonical live verification. These are not claims of new customer approval
requirements. Keep the local implementation separate from deployed status.
