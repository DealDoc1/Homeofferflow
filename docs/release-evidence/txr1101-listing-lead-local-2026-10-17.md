# TXR-1101 listing packet: seller lead disclosure — local checkpoint

## Outcome and release boundary

Selecting Paragraph 19 C, including the existing known-pre-1978 automatic
selection, now appends an actual seller-side TREC 56-0 to the composed listing
PDF. It is no longer merely listed as pending. This is implemented and locally
verified, **not deployed or completed-SignWell verified**.

Baseline: production/main `7b408eb09b46720261e8fed4712fe42e81547f33`;
preceding local packet checkpoint `a9697c672edceed5ec3102e8875e25af87425758`.
No migration, source registration, real invitation, billing change or production
deployment occurred in this batch. Git-triggered deployments remain disabled.

## Source and roles

- [Official TREC Form 56-0 page](https://www.trec.texas.gov/node/3086),
  retrieved October 17, 2026: printed May 4, 2026, effective May 28, 2026.
- Existing bundled static source SHA-256:
  `eb8bdfb943cafbe8402e6b44fe44d73eb66d6acd6a99f31f73498f938fd76e6c`.
- Fresh official fillable download SHA-256:
  `515bda0aa4b834e55b0fe894378e8ce200c9c3547c81fcb11bf1019107dbf868`.
  It has 25 native fields; the static copy has none. Extracted text and all
  4,464 text/position tuples rounded to .01 point match. No source binary was
  replaced, committed anew or modified.
- Seller 1 completes unanswered disclosure choices; one or two Sellers and the
  already selected listing associate/broker sign their printed execution rules.
  No Buyer, Buyer's Broker, receipt acknowledgement or inspection waiver is
  populated or added as a signer. Invitations remain parallel.

## Answer and delivery contract

The interview defaults both seller topics to unanswered. Explicit seller facts
can be entered and saved, reopened, then printed on measured source blanks or
lossless continuation pages. Inactive negative-branch details are not printed.
Unanswered topics use unchecked, required exact-one checkbox groups, never a
preselected factual answer. A positive answer conditionally requires its missing
explanation on an initialed details page. Live explanation fields wrap, fit
within the provider's text-field height, and accept 1–200 characters; longer
known answers entered in the interview retain the existing 4,000-character
continuation route. Supporting reports are not fabricated or silently attached.

Packet composition namespaces group/rule references with field IDs and remaps
only reviewed recipients. It rejects dangling/cross-signer rules and more than
ten conditional rules. Packet confirmation and durable request fingerprints
bind the controls; requests without controls retain their legacy fingerprint.
The delivery coordinator compares persisted controls, text validation and
geometry before sending. Missing or changed controls leave an unsent provider
draft and surface the error. This is an implementation safeguard, not evidence
that the real provider has retained the new settings yet.

The [SignWell Create Document API](https://developers.signwell.com/reference/createdocument)
was checked for exact-selection groups, conditional requirements, wrapped text
and field height limits. The API bundle explicitly retains the pinned TREC
source and existing fonts in `includeFiles`.

## Verification

One final source-enabled focused run: **131 checks passed**, including renderer,
listing API, packet composition, control readback, durable delivery, IABS and
interview JavaScript wrappers. The expected simulated IABS-outage log is a
negative test, not a production failure. `git diff --check` passes.

The exact private TXR-1101 source was supplied with `HOF_TXR1101_SOURCE` to:

```sh
python -m unittest tests.test_listing_lead_disclosure tests.test_signwell_controls tests.test_txr1101_api tests.test_listing_packet tests.test_txr_1101 tests.test_txr1101_interview_runtime tests.test_signwell_delivery_adapter tests.test_signwell_delivery_coordinator tests.test_agent_iabs_profile -q
```

Four fictional QA PDFs / six rendered pages were visually reviewed: unanswered
single Seller, explicit negative answers/two Sellers, known facts/two Sellers,
and long Unicode continuation. Source X marks, signature/date boxes, empty
Buyer sections, continuation initials and 200-CJK-character live explanation
samples remain inside their reviewed blanks. These are simulated placement
guides, **not signed provider outputs**.

Desktop and 390×844 browser QA used the actual interview/queue with an isolated
mock transport and CSP denying external connections. Explicit facts persist
after save/close/reopen; deselecting C hides/disables the four lead controls;
known-pre-1978 reselects C. Phone document width equals 390 pixels with no
horizontal overflow. The fixture cannot send an invitation.

Evidence is outside Git, in this chat's `listing-lead-qa-2026-10-17` folder:
`manifest.json`, four PDFs, six page PNGs, `desktop-interview.png`, and
`mobile-interview.png`. Reproduce with `scripts/render_listing_lead_qa.py`
and the existing isolated `scripts/qa/txr1101_interview_fixture.cjs`.

## Remaining engineering work

Actual SignWell draft readback, fictional completed-provider signing and final
PDF visual QA are still required before this adapter is called provider-verified.
The primary listing source/schema activation and full frozen-candidate
regression/CI/intentional production release are also not done. Seller's
Disclosure Notice and water-rights adapters remain separate unfinished work;
do not bundle unverified disclosure PR #1341. No new owner sign-in, form-source,
seat or blanket approval requirement was introduced.
