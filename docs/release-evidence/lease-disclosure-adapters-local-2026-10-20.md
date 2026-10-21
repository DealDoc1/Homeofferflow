# Rental disclosure adapters — local checkpoint, October 20, 2026

Status: **implemented locally, focused tested and visually reviewed**. These
pure adapters are not connected to the hosted source loader or live send API.
No customer activation, provider-completed QA or production deployment is
claimed. Follows source-registration checkpoint `31e434aa`; documented live
baseline remains `bfd03d99` / shell v112, without another Vercel inspection.

## User outcome and scope

`lib/lease_disclosures.py` prepares the exact current downloaded TXR-2008 and
TXR-2015 sources for landlord-side preparation in the existing lease-listing
package. It does not choose tenants, acknowledge their receipt, load private
sources or send invitations. Access/ownership/version checks stay with the
existing API, not browser-supplied PDFs or field geometry.

- Pin both complete source hashes and revisions from the official download
  checkpoint; reject altered bytes. Validate one unencrypted Letter page,
  without native fields/widgets. Remove only the two exact supplier-added
  contact imprints, retaining original form, statutory/copyright and tenant text.
- TXR-2015 collects explicit landlord floodplain and prior-five-year flood
  knowledge. Unanswered is not No. Landlord 1 receives two exact-one choice
  groups; each actual landlord signs/dates. No agent or tenant is added to the
  flood certification.
- TXR-2008 keeps its own lead knowledge, report, signature and receipt geometry.
  Unanswered choices belong to Landlord 1; positive selections conditionally
  require explanations. Explicit facts are rendered only when supplied, with
  long/Unicode text preserved in continuations. Source statements about records
  supplied to a tenant remain the landlord's explicit statement, not an inferred
  delivery event. No tenant acknowledgement or receipt checkbox is populated.
- Only the existing listing professional signs the source's listing-professional
  line. The absent other professional and tenant lines stay untouched. One
  landlord never creates a second-landlord field.
- The returned `remaining_actions` explicitly reserves tenant receipt/signature
  for a later tenant-participation flow. Integration must carry that message
  into the review/status contract; an included landlord-preparation PDF is not
  proof of a completed tenant disclosure, supporting-report delivery or delivery
  of the required lead pamphlet.
- Stable fingerprints bind exact source, adapter revision, landlord identity,
  property, explicit answers, fields and completion controls—not renderer time.
  Package composition retains explicit recipient maps and namespaces/offsets
  both source-specific controls without adding recipients.

## Verification

```sh
HOF_LEASE_DISCLOSURE_SOURCES='../lease-listing-2026-10-20/sources' \
HOF_TXR1102_SOURCE='../listing-source-2026-10-17/sources/TXR-1102-2026-01-05.pdf' \
  ../txr1101-runtime/bin/python -m unittest \
  tests.test_lease_disclosures tests.test_lease_listing_packet \
  tests.test_listing_packet tests.test_listing_lead_disclosure -q
```

Result: **48 tests, one unrelated source opt-in skip, exit 0**. All 14 new
adapter tests ran against the actual private sources. Coverage includes strict
answer contracts, non-inference, source hash rejection, source/legal text
retention, untouched originals, four flood-choice branches, both professional
plans, one/two landlords, live conditional explanations, single-landlord dates,
all field bounds/control references, stable/tamper-sensitive fingerprints,
lossless long/Unicode continuation and real 14-page primary+two-disclosure
composition. Sale listing/lead composer regression remains clean. `git diff
--check` passes. No full-suite repeat was made for these unconnected adapters.

The PDF skill drove six clearly fictional local field-placement proofs using
`scripts/qa/prepare_lease_disclosure_layout.py`: ordinary, single-negative and
long/Unicode for each source. Nine pages total; all nine were visually reviewed
after accounting for the corrected source page. The blue guides show every
potential control, not actual selected landlord answers. These specimens are
not normal customer documents and were not sent or offered as deliverables.
Private artifacts live under
`../lease-listing-2026-10-20/disclosure-output/{pdf,tmp/pdfs}/`.

The first review found TXR-2008's lower signature boxes covering the preceding
printed row labels. Those source rows have only 28pt between execution lines.
The lower signature fields now use 13.5pt height and adjusted baselines; date
fields keep MM/DD/YYYY, locked signing dates and 54pt width. A new actual-source
character-intersection assertion proves no signature/date rectangle overlaps
original printed text. The three changed lead source pages were re-rendered
and re-reviewed; unchanged continuation/flood pages were not regenerated again.
This is local layout evidence, not a claim that SignWell's final output has
already passed the new smaller signature-field placement check.

## Next release work

1. Connect these adapters to verified central private sources and existing lease
   package APIs; add source-intake/catalog support for TXR-2008/TXR-2015. Their
   source PDFs are already downloaded, not yet registered remotely. Do not
   request another source-owner authorization, brokerage seat or member sign-in.
2. Bind actual source/revisions and reviewed packet state through retries;
   preserve meaningful pending tenant/report/pamphlet tasks without stopping the
   main listing flow. Add focused isolated API tests and customer review checks.
3. Complete changed provider-rendering QA, exact-head regression/CI and the
   coordinated code/schema release, then canonical production smoke checks.

No network request, browser action, hosted SQL, permission change, invitation,
email, charge or deployment occurred in this adapter slice. Worktree checkpoint
does not mark the broader lease workflow or roadmap complete.
