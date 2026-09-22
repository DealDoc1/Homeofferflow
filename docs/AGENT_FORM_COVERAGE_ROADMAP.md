# HomeOfferFlow — Agent Form Coverage Roadmap

Future batches follow the [lean development protocol](LEAN_DEVELOPMENT_PROTOCOL.md)
to reduce model context, repeated regression runs and Vercel usage without
reducing verification standards.

TREC-62-0 now has a source-backed Seller-notice implementation for removing
the backup-contract contingency after the first contract has ended. The guided
interview collects the property, Buyer names, Seller names, and known delivery
date; only Sellers are signing recipients, invitations are parallel, and both
escrow-agent receipt sections remain blank. It is available to every signed-in
agent without a brokerage seat. The renderer, source allowlist, database
constraint, signing map, and purchase-document interview are locally
implemented and under release QA; production deployment is not yet claimed.

## Local continuation status - September 18, 2026

Authenticated entry, billing, help, brokerage, seller-lead and partner-plan
surfaces now describe customer actions instead of internal “workflow” language.
Generic help copy also says “signing” rather than exposing the SignWell vendor
name. Event names, API fields, prices, entitlements and transaction behavior
are unchanged. One hundred five focused tests pass. This is **locally
implemented and tested, not deployed**. See [authenticated language evidence](release-evidence/authenticated-plain-language-cleanup-2026-09-18.md).

The homepage and six primary public acquisition pages now use direct customer
actions instead of visible internal “workflow” language. Buyer, agent,
investor and partner copy now explains the next action in plain language;
routes, pricing, analytics, structured data and legal behavior are unchanged.
Eighteen focused tests pass, including visible-text checks across the homepage,
buyer, seller, agent, investor, partner and directory pages. This is **locally
implemented and tested, not deployed**. See [public language evidence](release-evidence/public-landing-language-cleanup-2026-09-18.md).

Future bounded workstreams can now start from a live, compact repository
handoff instead of replaying this task's full conversation. The generator
captures the five required batch facts, current branch/commit, at most 20
changed paths and eight recent commits; it reads no browser state, environment
variables, credentials or file contents. Three focused tests and a real
worktree run pass. This is a **local development-process improvement, not a
production deployment**. See [lean handoff evidence](release-evidence/lean-handoff-generator-2026-09-18.md).

Resend suppression-list additions/removals are now recognized locally by the
existing secure webhook and surfaced as privacy-safe aggregate admin metrics.
New additions become email-delivery attention items without distorting the
confirmed-delivery rate. This requires no polling or new paid service and is
**locally implemented, not deployed**. See
[suppression visibility evidence](release-evidence/resend-suppression-visibility-2026-09-18.md).

Completed-provider geometry checks for six corrected forms were consolidated
into one nonbinding SignWell document instead of six separate requests. Both
approved QA recipients completed the 14-page, 54-field packet, and every page
of the provider-produced PDF passed visual placement review. Its provider
document ID is `4ec37d4c-4283-4933-8416-28866c15f918`; its final SHA-256 is
`59c9959922eb3cee8c6ca8c6c5de14c445817829670603201588a59c79f6e3e2`.
Both signing-map baselines are now locked to the reviewed geometry; 13 focused
checks and the complete 2,333-test repository suite pass. See
[compact SignWell QA evidence](release-evidence/compact-signwell-geometry-qa-2026-09-18.md).

The bundled purchase-packet golden manifest now matches the visually approved
execution geometry for financing, appraisal, HOA, sale-contingency, and backup
addenda. A fresh two-buyer packet confirms every corrected signature and
initials rectangle stays on its printed Buyer rule or footer blank, while
unprinted date widgets remain removed. The exact cross-platform CI rendering
guard passes locally. See
[bundled golden-baseline evidence](release-evidence/bundled-packet-golden-baseline-2026-09-21.md).

The seven-commit signing-reliability stack is now merged into `main` through
PR #1233 at `b4d517be`. Post-merge GitHub Actions run `35404761878` passed the
full unit suite, golden packet rendering, standalone signer-geometry guard,
Supabase preflight, and whitespace check. The intentional production workflow
skipped and Git-triggered Vercel deployments remain disabled, so this is
**merged and CI-verified, not production-deployed**. See
[signing-reliability merge evidence](release-evidence/signing-reliability-main-merge-2026-09-18.md).

Live release revalidation at approximately 4:25 PM America/Chicago confirms
Vercel reports the September 15 production revision, not the local candidate.
The Pro usage credit is exhausted with $1.39 on-demand usage already recorded;
the displayed cycle resets September 22. Five database migrations required by
the pending batch are also absent from production, confirmed by catalog reads.
These are verified release dependencies, not a new login or customer approval
requirement. See [current release evidence](release-evidence/production-release-revalidation-2026-09-18.md).

The backup-contract addendum now has source-aligned Buyer initials/signatures,
no extra unprinted date fields, bounded answers on both pages, and complete
initialed overflow attachments. Explicit zero fees remain visible. Seven
rendered pages pass visual review, and offline production requests preserve
parallel invitations and later repair-page offsets. This is **not deployed or
completed-provider verified**. See [backup-contract evidence](release-evidence/backup-contract-layout-2026-09-18.md).

The sale-of-other-property addendum now uses measured answer blanks and Buyer
signature boxes without extra date fields. Zero additional earnest money is
preserved, long answers continue intact on initialed attachments, and later
addendum pages remain correctly mapped. Six rendered pages and offline
parallel-invitation cases pass. This is **not deployed or completed-provider
verified**. See [sale-contingency layout evidence](release-evidence/sale-contingency-layout-2026-09-18.md).

The HOA addendum correction is now locally implemented and visually reviewed:
bounded text and complete overflow attachments, smaller source-cell marks,
source-aligned Buyer signatures without unprinted date fields, and correct
following-page offsets. The interview now asks the previously missing updated
resale-certificate question only when documents were already received, hides
irrelevant delivery days, and includes HOA terms in review. Actual mobile and
desktop browser checks and six rendered source-backed pages pass. This is
**not deployed or completed-provider verified**. See
[HOA interview and layout evidence](release-evidence/hoa-interview-layout-2026-09-18.md).

The purchase-offer appraisal addendum now uses the same bounded, editable
answer layout as standalone TXR-1948. Buyer signature boxes follow the source
rules without extra unprinted date fields; continuation pages receive Buyer
initials and shift following addenda correctly. Source hashes and render
revisions remain recorded. Local rendered/offline-payload checks pass; this is
**not deployed or completed-provider verified**. The long-address specimen
also exposed clipping on the following HOA addendum, now covered by the
separate local correction above. See
[combined appraisal evidence](release-evidence/purchase-appraisal-candidate-2026-09-18.md).

Standalone TXR-1948 appraisal-addendum answers now stay within measured source
blanks or continue intact on an initialed attachment. Editable fields retain
matching canonical values and embedded Unicode appearances; preview names no
longer overlap, and signing copies leave execution lines clear. All five pages
of three source-backed candidates were visually checked, with offline delivery
coverage for every buyer/seller combination. This is **locally tested, not
deployed or completed-provider verified**. The combined purchase-offer renderer
is covered by the separate follow-on correction above. See
[appraisal answer evidence](release-evidence/txr1948-answer-candidate-2026-09-18.md).

Generated mineral-reservation, loan-assumption, residential-lease and
fixture-lease addenda now remove the original supplier's contact imprint from
the four exact reviewed blank sources. All five affected pages pass strict
before/after content and pixel checks, and were visually reviewed. Official
form text and attribution, entered names, and signature positions remain
unchanged. This is **locally tested, not deployed**; see
[addendum source-imprint evidence](release-evidence/addenda-source-imprint-2026-09-18.md).

TXR-1953 residential-lease and TXR-1954 fixture-lease answers now fit measured
source blanks or continue in full on paginated, party-initialed attachments.
All eight pages of four source-backed specimens were visually checked.
Offline standalone delivery covers all buyer/seller combinations and parallel
invitations; combined-purchase checks preserve continuation offsets and seller
recipient IDs. Existing base signature rectangles and checkbox centers are
unchanged. This is **locally tested, not deployed or newly provider-completed
verified**; see [lease-addendum answer evidence](release-evidence/lease-addenda-answer-candidate-2026-09-18.md).

Standalone PDF deployment configuration now retains the fonts needed by the
representation renderers. Fresh-process tests cover all four forms and their
long-answer continuations; non-PDF services still omit these assets. Private
QA/output directories are explicitly excluded from Git and Vercel uploads.
This is **locally tested, not deployed**; see
[runtime-asset evidence](release-evidence/pdf-runtime-assets-2026-09-18.md).

TXR-1506 consumer-notice answers now fit measured source areas; the signing
copy no longer prints consumer names underneath their signature fields.
Consumer-identification headers remain populated, and long names/notices
continue in full with required initials for the same selected recipients.
All 26 pages of four synthetic signing specimens were visually checked.
Base signature/date/initials coordinates are unchanged. This is **not deployed
or newly completed-provider verified**; see
[consumer-notice evidence](release-evidence/txr1506-answer-candidate-2026-09-18.md).

Representation PDF identity and broker recipients now resolve from the agent's
own profile/optional active organization, not the shared source host. No-seat
associate use and a consistent render/recipient snapshot are locally tested.
This is **not deployed or live-provider verified**. See
[professional-identity evidence](release-evidence/representation-professional-identity-2026-09-18.md).
Supplier footer details are now removed from generated copies of the four
exact reviewed representation sources. All 15 pages pass before/after pixel
checks above the footer under bundled and production-pinned PDF libraries.
Original sources, official attribution and form geometry remain unchanged.
This is **not deployed**; see
[source-imprint evidence](release-evidence/txr-source-imprint-2026-09-18.md).
The showing form (TXR-1508) now has locally corrected answer baselines, bounded
name/address placement, a selected-associate check and lossless long-answer
continuations with matching customer/professional initials. All six pages of
four synthetic specimens were visually checked. Existing base-page initials
and date positions are unchanged. Completed-provider QA of the new
continuations and deployment are still outstanding; see
[showing-form answer evidence](release-evidence/txr1508-answer-candidate-2026-09-18.md).
Independent separate-broker contact entry is now implemented in the existing
recipient-review screen, with saved-request recovery and no seat requirement.
Local runtime and mobile/desktop browser checks pass; this is **not deployed or
live-provider verified**. See
[independent-broker evidence](release-evidence/independent-broker-signing-2026-09-18.md).

TXR-1507 short-form answer review found misplaced lease-compensation values and
overflow risks. Supported values now fit source-measured blanks or continue in
full on an initialed attachment. Both role previews and long-answer variants
were visually checked; base execution positions are unchanged. This is
**not deployed or newly completed-provider verified**. See
[short-form answer evidence](release-evidence/txr1507-answer-candidate-2026-09-18.md).
The short-form interview now also follows the selected service scope: Showing
Services does not ask for or print inapplicable full-service compensation or
intermediary answers. Choice switching preserves open-dialog inputs. Local
browser, parser and PDF checks are recorded in
[service-interview evidence](release-evidence/txr1507-service-interview-2026-09-18.md).
This remains **not deployed or live-provider verified**.

TXR-1501 long-form execution review found the associate mapped below the printed
name, not on the shared broker/associate signature rule. That map and narrow
date boxes are corrected locally, with independent source-bound tests and
two rendered role previews. This is **not deployed or provider-completed QA**.
See [long-form execution evidence](release-evidence/txr1501-execution-candidate-2026-09-18.md).
The full-value review also corrected continuation headers, contact and term
placement, compensation/retainer blanks, protection days, county placement and
both intermediary marks. See [long-form value evidence](release-evidence/txr1501-value-candidate-2026-09-18.md).
The local preview now exercises these fields instead of leaving them empty.
Footer initials are now included locally for every selected signer on pages
1-5, with source-bound tests and rendered review. See
[initials evidence](release-evidence/txr1501-initials-candidate-2026-09-18.md).
Completed-provider placement remains unverified for the long-form candidate.
Long answers now wrap within measured blanks or continue in full on an attached
answer continuation, with required initials for the same selected signers.
The actual rendered page count controls those extra fields. This is locally
tested and visually reviewed, not deployed. See
[long-answer evidence](release-evidence/txr1501-overflow-candidate-2026-09-18.md).
Standalone sending now also uses one owner-scoped draft snapshot and a single
approved-source download, removing three duplicate reads without changing the
user workflow. Real-render offline integration tests cover short/long forms,
continuations and concurrent edits. This is **not deployed or live-provider
verified**; see [send-snapshot evidence](release-evidence/txr-render-send-snapshot-2026-09-18.md).

Environmental-review TXR-1917 now has a locally tested purchase-interview and
combined-packet candidate, including source-bound placement and long-answer
continuations. It is **not deployed** and its completed-provider placement
remains unverified. See
[the environmental packet evidence](release-evidence/environmental-purchase-packet-2026-09-18.md).
This does not change the production-status claims below or mean all remaining
form work is complete.

Loan-assumption TXR-1919 now has a locally connected purchase interview and
combined packet with exact-cent totals, conditional questions, shared sellers,
draft restoration and browser-to-PDF checks. Completed-provider placement and
live source retrieval are unverified. It is **not deployed**. See
[the loan-assumption interview evidence](release-evidence/loan-assumption-interview-2026-09-18.md).
The cash-switch check exposed existing whole-dollar rounding outside the
assumption path. Collector/calculator/PDF precision is now corrected locally,
with five-financing-type packet checks and conventional-to-cash browser checks.
Financing rate/fee placement was corrected after three-decimal values exposed
overlaps. See [currency precision evidence](release-evidence/purchase-currency-precision-2026-09-18.md).
This remains **not deployed**. Loan-assumption self-service checkout now has a
locally tested prepayment packet check using the fulfillment builder. Offline
integration checks preserve exact totals through saved checkout data and the
simultaneous-signing request; failed checks preserve interview answers for retry.
See [checkout evidence](release-evidence/loan-assumption-checkout-2026-09-18.md).
Live payment, private-source retrieval, delivery and completed-provider placement
remain unverified for this combined path; the full customer journey is not yet
claimed production-ready.

## Launch scope: OnDemand Realty

The OnDemand launch includes the current **purchase-offer packet** and its
supported purchase addenda, including the Seller Temporary Residential Lease
when seller post-closing possession applies. Signed-in agents can start guided
relationship, consumer-notice, seller-disclosure, seller-financing,
mineral-reservation, loan-assumption, environmental-review, appraisal-review,
and lease-addendum workflows, plus private seller-planning workspaces.
All released TXR workflows—TXR-1501, TXR-1506, TXR-1507, TXR-1508,
TXR-1905, TXR-1914, TXR-1917, TXR-1919, TXR-1948, TXR-1953, and TXR-1954—
plus TREC-62-0 Seller Notice of Removal of Backup-Contract Contingency—
have a separate review-and-send path: the agent reviews the completed document
and explicitly confirms each recipient before SignWell receives it. TREC-55-1
seller disclosure and optional TREC-61-0 water disclosure are available from
the shared library to every authenticated agent; after seller review and agent
recipient confirmation, the disclosure can be sent for signature and the
completed PDF is available in that agent's private workspace. The released shared library does not require a brokerage seat or a per-agent brokerage attestation. It is not represented as a complete transaction-form library or a transaction-management platform.

Preparation and sending remain intentionally separate: the agent must review
the completed document and confirm every recipient before a signature request
is sent. Listing agreements and any other document not expressly available for
its stated use in HomeOfferFlow remain separate workflows.

The authenticated agent dashboard now includes a **Request a missing form**
action. It routes the request into the existing support/feedback queue with a
form-request category and asks for the transaction role and intended workflow;
agents are instructed not to include confidential client information. A
request records demand only—it never unlocks, generates, or sends a legal form.

This language appears on `/ondemand` before an agent begins the 60-day trial.

## What is live now

- Guided buyer-side offer preparation.
- The current production purchase contract workflow and its supported purchase
  addenda.
- Buyer electronic-signature delivery for the generated offer packet.
- Agent-supplied disclosure PDFs can be labeled, reordered, validated, and
  explicitly confirmed before they are appended to the offer packet. This
  preserves upload-only behavior: HomeOfferFlow does not generate, interpret,
  or sign a seller disclosure supplied this way.
- Seller Temporary Residential Lease (TREC 15-7) when the seller remains in
  possession after closing, including the defined buyer/landlord and
  seller/tenant execution roles.
- Agent accounts, OnDemand attribution, a 60-day card-required trial, and
  broker-level aggregate activity visibility with buyer and property details
  withheld.
- Review-and-send workflows for TXR-1501, TXR-1506, TXR-1507, TXR-1508,
  TXR-1905, TXR-1914, TXR-1917, TXR-1919, TXR-1948, TXR-1953, and TXR-1954
  for signed-in agents, where the approved source is available. Each requires
  the agent to review the prepared document and confirm the listed recipients
  before sending a SignWell request.
- Private seller leads and listing workspaces with launch planning, seller
  consultation briefs, and offer-comparison tools.

## Priority release order

### 1. Buyer representation agreement

The buyer representation workflow is available at the beginning of the buyer
relationship, before an offer is prepared. Draft preparation and signature
sending remain separate steps: the agent reviews the completed document and
confirms recipients before a request is sent.

Important source-form rule: TREC does **not** promulgate a buyer representation
agreement. For the Texas REALTORS® member workflow, the approved source forms
are TXR-1501 Residential Buyer/Tenant Representation Agreement - Long Form and
TXR-1507 Residential Buyer/Tenant Representation Agreement - Short Form. The
agent must choose the correct authorized form; HomeOfferFlow must not
silently default a client into either agreement or improvise legal agreement
language.

The supplied July 2026 Texas REALTORS® source-form inventory also identifies
TXR-1506 General Information and Notice to Consumers and TXR-1508
Unrepresented Customer Showing Form as closely related buyer-intake workflows.
They are separate releases, not addenda to a purchase offer.

Release requirements:

- a current, approved source revision in the HomeOfferFlow shared library;
- signed-in agent access to the released workflow without a brokerage-seat or
  per-agent-attestation requirement;
- an explicit agent choice between the Long Form and Short Form, with no
  preselected legal agreement;
- guided data intake limited to the approved agreement fields;
- correct agent, broker, and buyer signer/recipient roles;
- an explicit TXR-1507 signer plan (clients plus associate or clients plus
  broker) captured before a SignWell send action;
- secure association to the signed-in agent; a source-host organization may be
  retained for rendering and audit without becoming an access requirement;
- rendered-PDF, signature-placement, and single-/multi-buyer QA;
- HomeOfferFlow release authority approval before production release;

Foundation complete: the approved-source catalog supplies the released
TXR-1501, TXR-1506, TXR-1507, and TXR-1508 review-and-send workflows to every
signed-in agent. Source PDFs remain server-side and are never exposed as
downloadable browser URLs. A source-host organization may be retained for
audit and rendering, but it does not create an agent-access requirement.

The source-specific renderer and signer-map foundation is now released in
`lib/txr_1507.py`. It preserves the supplied two-page source, overlays only
validated intake values, and keeps the client one- and client two-signer maps
separate from the purchase-packet coordinates. Because the source includes a
brokerage execution line, the signer plan now requires clients plus the
authorized associate or clients plus the authorized broker; a client-only plan
is rejected. Source-coordinate overlays are re-rendered against the exact
private source so brokerage and client fields land on the printed
signature/date lines. The review-and-send step keeps recipient confirmation
separate from draft preparation. Private TXR-1507 previews revalidate
ownership and the active approved source revision on every request, and never
return a source URL.

The companion TXR-1501 Long Form workflow is now released in
`lib/txr_1501.py`. The authorized six-page source was visually inspected
page-by-page, and a sample overlay was rendered and checked for the party and
contact rows, market area, term dates, compensation, intermediary choice, and
printed-name areas. TXR-1501 drafts require the same deliberate signer-plan
choice as TXR-1507, and private previews use the approved source revision
without exposing its storage URL. The agent reviews the completed document and
confirms recipients before a SignWell request is sent.

### 2. Seller disclosure workflow

The seller disclosure workflow is live for TREC-55-1 and optional TREC-61-0
water disclosure drafts. It collects seller responses, preserves the seller's
review responsibility, supports a secure review link, and after review lets
the agent confirm the named signing recipients before starting the signature
request. The agent can refresh status and download the completed PDF from the
same private workspace.

Build this as a seller-side workflow, separate from the buyer offer wizard.
It must collect seller responses, preserve the seller's review responsibility,
and route the completed disclosure to the correct recipients. It must not be
confused with the purchase contract's question about whether a disclosure has
already been received.

Release requirements:

- use the current approved disclosure form and version;
- seller-only questionnaire and electronic-signature workflow;
- property and listing association with access controls;
- visible review/attestation step for the seller;
- rendered-PDF and field-by-field QA;
- HomeOfferFlow release authority approval before production release.

### 3. Listing agreement workflow

Build this as the opening of the seller/listing workspace, paired with the
seller disclosure workflow rather than as another offer addendum. Listing
agreements are usually organization-private agreements, so the source owner
must supply the authorized source agreement and attest to its use before
implementation.

Release requirements:

- authorized source agreement and version owner;
- seller, listing agent, broker, and any team/supervisor roles defined by the
  source-owning organization;
- listing-specific data intake and electronic signatures;
- visibility limited to the assigned organization team and authorized
  administrators;
- rendered-PDF, signature-placement, and multi-seller QA;
- HomeOfferFlow release authority approval before production release.

### 4. Core transaction follow-up forms

After the relationship and listing foundations are live, add the documents
agents most often need after an offer is written: approved amendments,
termination/notice workflows, and remaining authorized transaction forms.
Each form is a separate release, not a checkbox added to the offer wizard.

## Non-negotiable release gate for every new form

1. **Approved source:** confirm the official or source-owner-authorized form,
   current version, and authority to use it.
2. **Data model:** add only the information needed for that document and keep
   buyer/seller data separated by role.
3. **Signing plan:** define each recipient, signing order, and applicable
   organization oversight before any e-signature fields are placed.
4. **Visual QA:** inspect every applicable blank, checkbox, initial, signature,
   and date on a rendered completed PDF.
5. **Regression:** add a dedicated golden test packet for the new form and run
   existing purchase-packet regressions.
6. **Release authority:** HomeOfferFlow's CEO or delegated product reviewer
   signs off on the workflow and release copy before production. If a customer
   brokerage or organization supplies a private source, its authorized source
   owner must separately attest to the source and version.

## Communication rule

Until each workflow passes the release gate, sales, onboarding, and the product
UI must say **"currently supported purchase-offer packets and addenda"** —
not "all agent forms," "complete transaction management," or equivalent broad
claims.
