# AI offer-review benchmark guardrails

HomeOfferFlow's offer-review feature is an educational decision-support tool.
It is not a valuation, legal opinion, broker direction, fiduciary advice, or a
prediction that an offer will be accepted.

## What the automated benchmark protects

The regression suite uses fixed, non-property-specific terms to ensure the
rules-based fallback continues to behave sensibly when live AI or public
property context is unavailable:

| Scenario | Expected behavior |
| --- | --- |
| Same conventional offer on a fresh, hot listing | Score decreases and reflects strong seller leverage. |
| Same conventional offer on a stale listing with reductions/motivation | Score increases and reflects strong buyer leverage. |
| Weak offer terms | Risks identify the sale contingency, seller concessions, and long option period. |
| Any fallback result | Score stays within 1–100 and includes the educational disclaimer. |

Run it with:

```bash
PYTHONPATH=/private/tmp/homeofferflow_test_deps \
python3 -m unittest tests.test_ai_offer_review_benchmark
```

## What this does not prove

This benchmark does not certify market accuracy, property valuation, or live
Gemini output quality. Before expanding the AI feature beyond its current
limited release, compare a documented sample of anonymized, real transaction
scenarios against review by an experienced Texas broker or agent. Record where
the output was useful, misleading, or insufficient, then adjust the feature
without claiming it can replace professional judgment.
