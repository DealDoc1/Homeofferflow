# TXR-1501 footer initials — September 18, 2026

**Implemented and checked locally. Not deployed or completed-provider verified.**

## Finding and correction

The 06-15-26 private source has initials blanks for Broker/Associate and each
client on pages 1-5. The previous builder supplied only final-page signatures
and dates, so those footer blanks could not be initialed through its request.

The selected broker or associate and every named client now receive one required
initial field on each of those pages. One-client requests contain 14 total
fields (10 initials, four execution fields); two-client requests contain 21
(15 initials, six execution fields). There is no unused second-client field
when only one client signs, and no additional signer or approval is introduced.

The source underscore spans are:

| Role | Page 1 x span, PDF points | Pages 2-5 x span |
| --- | --- | --- |
| Broker/Associate | 325.982-361.064 | same |
| Client 1, excluding comma | 406.523-441.605 | 406.870-441.952 |
| Client 2 | 446.555-481.529 | 446.902-481.876 |

All share the footer text extent top=736.266, bottom=745.266. Widget coordinates
use SignWell's 96-DPI top origin: y=976, height=14; x=435/543/596. Width=46 for
the selected professional and second client, 45 for the first client to clear
the comma. The requested rectangles fit every measured page, not just page 1.
Actual provider artwork can differ from the requested widget bounds, so this
is not completed-provider proof.

## Request integrity

Updated the local map identifier to
`txr-1501-2026-09-18-execution-initials-candidate-v3`, accurately distinguishing
this candidate from the old completed-packet label. The existing revision
check rejects stale prepared copies; it does not alter existing sent or signed
agreements. No database, authentication, RLS, SDK or API-contract change was made.

## Verification

- 47 focused test methods pass across footer bounds, execution bounds, renderer,
  generic signer geometry and the actual server request dispatcher/verifier.
- Full discovery: 2,188 tests in 49.264 seconds; 2,186 pass and the same two
  approved-map comparisons fail. Log: `/private/tmp/hof-txr1501-initials-suite.log`.
- Both roles and both client counts are covered. Every initials field is
  required, uniquely identified and assigned to exactly one existing recipient.
- Mock provider response checks reject a missing initial, wrong recipient or
  wrong page. The preceding saved map revision is rejected by the existing
  stale-copy check. These are offline tests, not live provider acceptance.
- Rendered both two-client role specimens. Visually inspected the footer of
  every page 1-5 in each, ten footer views total. Synthetic initials sit in their
  own blanks and clear the role labels and comma. The PDF skill required these
  visual checks in addition to coordinate assertions.
- QA specimens/images remain private and untracked under
  `tmp/pdfs/txr1501-initials-review/`. The exact source and all customer agreements
  remain untouched. No signatures were applied to a customer document.

## Remaining verification

The approved reference maps are unchanged; the same two comparison tests still
identify pending map differences. No all-green/full-release claim is made.
Completed SignWell review remains needed for the long-form candidate, including
both professional roles and one/two-client layouts. Extreme-length free-text
fit/continuation review was subsequently completed locally; see
[long-answer evidence](txr1501-overflow-candidate-2026-09-18.md). That follow-up
advances the unpublished candidate to v4 and adds fields only when needed.

No public push, deployment, Vercel build, database mutation, customer email,
provider request, reminder, charge or new resource occurred.
