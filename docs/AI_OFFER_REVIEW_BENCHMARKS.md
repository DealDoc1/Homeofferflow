# AI Offer Review calibration benchmarks

The competitiveness review is educational software feedback. It is not a
comparative market analysis, valuation opinion, legal advice, broker advice,
or a promise that a seller will accept an offer.

## Purpose

`tests/test_ai_offer_review_benchmarks.py` protects the intended directional
behavior of the deterministic fallback engine. It is deliberately separate
from Gemini/public-web behavior so the product remains useful when live AI is
unavailable and so a provider/model change cannot silently reverse the core
logic.

## Current benchmark cases

| Case | What it protects |
| --- | --- |
| Clean cash offer | Strong seller-favorable terms remain strong when property-specific market data is absent. |
| Contingent, below-list offer | A low offer with long option period, FHA financing, sale contingency, and concessions scores materially weaker. |
| Hot versus stale listing | Identical moderate terms receive a materially lower score in a fresh/multiple-offer context than in a stale, reduced, seller-motivated context. |
| Component bounds | The five displayed score components remain present and within 1–100. |

## Release gate

Run the benchmark suite whenever the fallback scoring logic, the Gemini prompt,
or the UI score normalization changes:

```bash
PYTHONPATH=/private/tmp/homeofferflow_test_deps \
  /Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m unittest tests.test_ai_offer_review_benchmarks tests.test_ai_offer_review_rate_limit
```

The suite is a regression guardrail, not proof of market accuracy. Any
substantive scoring change still needs broker/expert review against a documented
real-world benchmark set before it is described as calibrated.
