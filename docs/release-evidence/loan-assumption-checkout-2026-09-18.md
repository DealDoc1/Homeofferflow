# Loan-assumption checkout — local evidence, September 18, 2026

Status: implemented and tested locally; not pushed or deployed. No customer
document was changed, no signature request or email was sent, and no payment
was created. This is not completed-signature placement QA.

## Change

Self-service checkout now accepts the guided loan-assumption financing choice.
Before initializing Stripe or saving a payable packet, the server calls the
existing Python fulfillment builder to validate terms and signers, retrieve the
private source, render the combined packet in memory and construct its signing
fields. Exact price, assumed balance and cash portion are returned to checkout
and persisted with the existing session binding and payload fingerprint.

An invalid answer, unavailable form, unverified response or failed service call
prevents payment from starting. The existing browser error path retains answers
and attachments and re-enables checkout for retry. This adds no user approval,
brokerage seat or form-source intake step.

## Security and operational boundaries

- A timestamped, domain-separated HMAC authorizes only the non-delivering
  preflight; it cannot authorize the paid-delivery handler. Five-minute freshness
  checks reuse the existing verifier.
- Requests use a fixed production origin or validated same-preview hostname,
  never a browser-supplied host, and cannot follow redirects. Payloads have a
  4 MiB limit and requests a 45-second timeout.
- Browser-supplied internal fields/source revisions are discarded. Source bytes
  remain server-side; only page count and monetary totals return. Unexpected
  service errors are redacted.
- Existing server-controlled price, private payload/session/email binding,
  webhook authority and simultaneous-signing behavior remain intact.
- No Supabase schema, RLS, authentication, storage policy or SDK changes. No new
  paid integration. Once deployed, each assumption checkout attempt adds one
  existing-function call and an in-memory render; ordinary checkout does not.
  No Vercel deployment/build was performed during this work.

Payment and Supabase skill guidance informed prepayment verification and private
source handling. Relevant official references:
[Stripe fulfillment](https://docs.stripe.com/checkout/fulfillment) and
[Supabase storage access control](https://supabase.com/docs/guides/storage/security/access-control).

## Verification

- Focused Python suite: 36 test methods passed across assumption checkout,
  checkout email delivery, payload integrity and fulfillment bridge.
- JavaScript runtime suites: 23 cases passed across assumption checkout and
  browser storage, including 422/503 retry without losing answers or attachments.
  Browser functions run in a simulated DOM, not a live browser in this turn.
- Full Python discovery: 2,176 tests; 2,174 passed, two existing signature-map
  baseline comparisons failed. No new full-suite failures. The later two browser
  retry cases passed in the separate JavaScript run; Python wrapper count is
  unchanged. Log: `/private/tmp/hof-assumption-checkout-suite.log`.
- Offline cross-language check: actual Node checkout calls actual Python
  preflight, then the captured payload passes the actual paid-session loader and
  fulfillment builder. The packet has 14 pages and retains price 500,000.55,
  assumed debt 270,000.35 and cash portion 230,000.20. The captured SignWell
  request has one file, buyer/seller recipients and `apply_signing_order:false`.
- External storage reads, Stripe, record writes, provider sends and email are
  mocked. Source PDF is a synthetic fixture with a test hash, not the live
  private source. No live SQL, actual checkout or email delivery is verified.
- Negative cases cover incomplete terms/signers, mixed financing, missing or
  changed source, absent/expired/tampered/wrong-purpose signatures, oversized
  requests and malformed responses. They do not initialize payment.

Existing full-suite failures:
`test_every_current_map_matches_the_source_calibrated_baseline` and
`test_current_released_maps_match_the_approved_baseline`. Baselines were not
updated to hide placement discrepancies.

## Remaining verification

The deployed shared secret, real private-source retrieval, platform request
duration, actual Stripe checkout/fulfillment and completed SignWell placement
remain unverified for this combined path. Availability can still change between
preflight and paid fulfillment; existing fulfillment recovery remains necessary.
Publication and deployment cost restrictions remain in force. Outstanding TXR
signer-variant placement checks and seller-financing combined-packet work remain
separate roadmap items.
