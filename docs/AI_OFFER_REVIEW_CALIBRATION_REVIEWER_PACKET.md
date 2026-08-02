# AI offer-review calibration reviewer packet

## Purpose

Use this packet to collect five independent Texas broker or agent reviews before
changing HomeOfferFlow AI scoring, ranking language, or recommendation wording.

This is a human-review evidence packet. It does not authorize a model change and
does not make the AI review legal, brokerage, or market advice.

## Reviewer requirements

Each reviewer should be a currently practicing Texas real-estate broker or
agent. The reviewer should evaluate the same anonymized scenario and generated
review output independently, without seeing another reviewer's disposition.

Do not include names, exact addresses, MLS numbers, client details, phone
numbers, email addresses, or confidential transaction information.

## Required scenarios

| ID | Scenario | Core question |
|---|---|---|
| AI-CAL-01 | Conventional financing; list-price offer; no sale contingency; seller-paid title policy; short option period; newly listed property with a highest-and-best deadline. | Does the review reflect strong seller leverage without treating the score as a prediction of acceptance? |
| AI-CAL-02 | Same terms; property listed for several months with price reductions and seller motivation. | Does the review distinguish stale-listing leverage and identify when the buyer may have more negotiating room? |
| AI-CAL-03 | Materially below-list financed offer; long option period; sale contingency; substantial seller concession; low earnest money. | Does the review identify each material seller-facing risk and explain tradeoffs? |
| AI-CAL-04 | FHA or other government-backed financing; appraisal protection selected; otherwise competitive price and ordinary option period. | Does the review explain financing/appraisal timing considerations without treating the financing type as inherently unacceptable? |
| AI-CAL-05 | Strong price and cash contribution; unusual closing or possession request; no reliable public market context. | Does the review disclose missing market context and avoid inventing property-specific facts? |

## Review form

Complete one copy per scenario:

- Reviewer role: broker / agent
- Scenario ID:
- Review date:
- Did the output accurately restate the entered terms? yes / no
- Did it identify the material tradeoffs? yes / no
- Did it distinguish entered facts from missing market context? yes / no
- Did it avoid predicting acceptance or presenting legal advice? yes / no
- Did it avoid treating financing type alone as a defect? yes / no / not applicable
- Most useful sentence or point:
- Misleading, missing, or overconfident point:
- Recommended disposition: keep / revise wording / revise scoring / do not use
- Reviewer notes:

## Evidence handling

Submit only anonymized notes through the in-app AI calibration feedback flow,
choosing the matching scenario ID and confirming the anonymization attestation.
The platform counts only agent, broker, or brokerage-admin notes tied to the five
documented IDs toward the calibration tracker.

A generated AI review output is not calibration evidence by itself. The release
gate remains open until all five scenario IDs have independent human review
evidence, the dispositions are reconciled, and product release authority
approves any resulting change.

## Release gate

Before changing scoring or wording, record:

1. One or more independent reviewers for each scenario ID.
2. The anonymized review records and dispositions.
3. The proposed wording/scoring diff.
4. Regression results for the existing golden scenarios.
5. Product release authority approval.
