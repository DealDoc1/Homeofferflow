# Price and financing checks before paid checkout

## Confirmed issue and local implementation

`api/create-checkout.js` previously checked the requested product/price and
receipt email but passed arbitrary offer data to Stripe without validating
its price and financing answers. Browser-only Continue validation could be
bypassed by a stale or direct request.

The endpoint now rejects invalid offer shapes and the same required numeric
answer categories checked in the interview before initializing Stripe:

- Positive purchase price, financed loan amount, and loan term.
- Nonnegative earnest money, option fee, interest rate/cap years, origination
  cap, and selected appraisal values.
- Safe nonnegative whole-number option, buyer approval, and selected appraisal
  termination day counts.
- A financing choice supported by the existing packet renderer: cash,
  conventional, FHA, VA, or USDA. Cash ignores inactive loan fields.

Zero fees, zero-day periods, zero interest, and decimal amounts remain valid.
No loan-to-price ratio or speculative maximum price/rate was imposed. Existing
price/earnest aliases are supported, but an invalid explicitly supplied primary
field cannot be concealed by an alternate alias. Error messages identify
answers to review without reflecting submitted values.

Receipt email is type-checked, syntax-checked, and trimmed consistently for
Stripe and metadata. The payments skill guided keeping the product price,
redirect safeguards, payment mode, and webhook behavior unchanged. No settings,
existing customer payments, or subscriptions were modified.

## Verification

- 101 source-backed API runtime cases pass with a mocked Stripe SDK.
- Against pre-fix commit `2f132155`, 94 new validation/boundary cases fail and
  seven existing valid controls pass.
- Invalid requests assert HTTP 400, zero Stripe session calls, and zero Stripe
  initializations. Valid requests assert one session, the server-owned Price,
  and round-trip preservation of entered values in fulfillment metadata.
- Existing plan, client-price override, and anchored-redirect tests now supply
  a complete valid cash-offer pricing fixture and retain their prior checks.
- API syntax and `git diff --check` pass. Full local suite: **2,002 tests pass
  in 17.762 seconds**.

This is local API contract testing, not live Stripe checkout or payment QA.
This validator covers price/financing data only; it is not a full legal,
document-readiness, signer-identity, or server-side contract-validity check.

## Release/cost status

Local only; no live checkout, push, Vercel build, preview, or production release.
No new service, dependency, fee, or recurring task added. Include in the next
authorized cost-controlled release and daily report as locally verified.
