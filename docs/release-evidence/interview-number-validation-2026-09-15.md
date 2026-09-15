# Price and financing interview: numeric answer feedback

## Confirmed issue and local change

The pricing step required nonempty strings but did not validate numeric bounds.
Negative amounts, non-finite inputs in restored/programmatic field values,
fractional option days, and zero offer prices could pass Continue. The input
feedback helper also cleared a warning whenever any nonempty text appeared.

A shared validator now applies to the 13 defined pricing, financing, deposit,
and appraisal fields already required by the relevant interview branches.
Offer price, financed loan amount, and loan term must be positive. The other
amounts and rates permit zero. Option days, buyer approval days, and appraisal
termination days must be nonnegative safe whole numbers. Decimal monetary
values and rates remain accepted. No speculative maximum rate, price, loan
ratio, fee amount, or appraisal policy was introduced.

Required-field feedback reports the field and expected value, marks it with
`aria-invalid`, and keeps the existing first-invalid-answer focus guidance.
The live correction handler retains warnings for still-invalid numeric
answers and does not clear the step summary while another invalid answer
remains. Fields outside this allowlist keep their prior behavior.

## Verification

- 48 focused source-backed runtime cases pass, exercising actual step
  validation and correction handlers for homebuyer, agent, and investor roles.
- Pre-fix commit `5639ffb6`: 29 cases reproduce invalid acceptance or premature
  warning removal; 19 valid/existing-behavior controls pass.
- Covers all 13 negative-value fields, malformed/non-finite numbers, unsafe
  or fractional day counts, explicit zero choices, positive-value requirements,
  decimal amounts, cash-only hidden-loan behavior, accessible error state,
  multi-field corrections, and unchanged unlisted-field behavior.
- Full local suite: **2,001 tests pass in 17.419 seconds**.
- All 45 executable inline scripts parse; `git diff --check` passes.

This verifies client-side Continue validation in a mocked DOM, not live browser
validation, contract sufficiency, or server-side request rejection. It does not
claim a production packet/payment integration test or change contract text.

## Release and cost

Local only. No push, Vercel build, preview, deployment, customer email, or paid
service. Include in the next authorized cost-controlled release and daily
report as locally verified until production is tested.
