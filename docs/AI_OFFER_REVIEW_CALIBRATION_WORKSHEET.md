# AI offer-review calibration worksheet

This worksheet is for an experienced Texas broker or agent reviewing the
educational offer assessment. Use anonymized transaction facts only. Do not
enter client names, exact property addresses, MLS numbers, or other direct
identifiers.

The reviewer is evaluating whether the output is useful, misleading,
insufficient, or missing—not approving an offer and not providing a legal or
valuation opinion.

## Review instructions

For each scenario:

1. Enter the scenario facts into HomeOfferFlow.
2. Save the result and record the displayed score, market mode, strengths,
   risks, suggestions, and market context.
3. Compare the result with your professional assessment of the scenario.
4. Record any material error, unsafe implication, missing factor, or wording
   that could mislead a buyer or agent.
5. Submit the feedback through **Review this result** using issue type
   `AI offer review`, or attach the completed worksheet to the internal QA
   record.

Do not change scoring or present the feature as calibrated until at least five
scenarios have been reviewed and the disagreements have been documented.

## Scenario set

| ID | Anonymous facts | Expected calibration question |
|---|---|---|
| AI-CAL-01 | Conventional financing; offer at list price; no sale contingency; seller-paid title policy; short option period; newly listed property with a highest-and-best deadline. | Does the review appropriately reflect strong seller leverage without treating the score as a prediction of acceptance? |
| AI-CAL-02 | Same terms as AI-CAL-01; property has been listed for several months with multiple price reductions and seller motivation. | Does the review distinguish stale-listing leverage and identify when the buyer may have more negotiating room? |
| AI-CAL-03 | Financing offer materially below list price; long option period; sale-of-other-property contingency; substantial seller concession; low earnest money. | Does the review identify each material seller-facing risk and avoid recommending a change without explaining the tradeoff? |
| AI-CAL-04 | FHA or other government-backed financing; appraisal protection selected; otherwise competitive price and ordinary option period. | Does the review accurately describe financing/appraisal timing considerations without implying the financing type is inherently unacceptable? |
| AI-CAL-05 | Strong price and cash contribution; unusual closing or possession request; no reliable public market context available. | Does the review disclose the missing market context and focus on the entered terms instead of inventing property-specific facts? |

## Per-scenario record

Copy this block once for each ID above.

```text
Scenario ID:
Date reviewed:
Reviewer role/experience (no name required):

Displayed score:
Displayed market mode:
Displayed source/model:

Professional assessment of the offer posture:

Useful output (what helped):

Misleading or unsafe output (quote/paraphrase only; no client identifiers):

Insufficient or missing factor:

Did the disclaimer remain clear?  Yes / No
Did the output imply acceptance, valuation, legal advice, or broker direction?  Yes / No

Recommended wording or scoring change:

Reviewer disposition: Useful / Needs revision / Unsafe until revised
```

## Release decision

Record the aggregate result before changing the model or fallback rules:

- Scenarios completed: `__ / 5`
- Useful without material correction: `__`
- Needs wording revision: `__`
- Needs scoring/calibration revision: `__`
- Unsafe or blocked from expansion: `__`
- Expert reviewer conclusion:
- Owner of any follow-up change:
- Re-test release and date:

The AI review remains a limited educational feature until this section is
completed and the resulting changes pass the existing bounded-output and
disclaimer tests.
