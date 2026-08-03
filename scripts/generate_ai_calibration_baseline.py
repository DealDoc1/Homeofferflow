#!/usr/bin/env python3
"""Generate anonymized deterministic outputs for the AI calibration packet.

This report is a technical baseline for reviewers. It is deliberately not
calibration evidence: only independent, anonymized broker/agent notes submitted
through the authenticated feedback flow count toward the release gate.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs" / "AI_OFFER_REVIEW_CALIBRATION_FIXTURES.json"
OUTPUT = ROOT / "docs" / "AI_OFFER_REVIEW_CALIBRATION_BASELINE.json"
MODULE_PATH = ROOT / "api" / "ai-offer-review.py"


def _load_review_module():
    spec = importlib.util.spec_from_file_location("hof_ai_offer_review", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the AI review module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _offer_for_fixture(scenario):
    price = 500000
    price_vs_list = scenario["price_vs_list"]
    if price_vs_list == "at_list":
        offer_price = price
    elif price_vs_list.endswith("%"):
        offer_price = round(price * float(price_vs_list[:-1]) / 100)
    else:
        offer_price = price

    earnest_text = str(scenario["earnest_money"]).rstrip("%")
    earnest = round(price * float(earnest_text) / 100)
    financing = scenario["financing"]
    if financing == "government_backed":
        financing = "fha"

    offer = {
        "offerPrice": str(offer_price),
        "listPrice": str(price),
        "earnestMoney": str(earnest),
        "optionFee": "250",
        "optionDays": str(scenario["option_days"]),
        "financing": financing,
        "saleContingency": "yes" if scenario["sale_contingency"] else "no",
        "concessionAmount": str(scenario["seller_concessions"]),
        "wantsConcessions": "yes" if scenario["seller_concessions"] else "no",
        "appraisalAddendum": (
            "partial" if scenario["appraisal_posture"] == "appraisal_protection_selected" else "none"
        ),
        "titlePayer": "seller" if scenario["id"] == "AI-CAL-01" else "buyer",
        "titleAmendment": "seller" if scenario["id"] == "AI-CAL-01" else "buyer",
        "survey": "buyerNew",
        "asIs": "no",
        "possession": "funding" if scenario["id"] != "AI-CAL-05" else "sellerTemporaryLease",
        # Keep the technical baseline focused on offer competitiveness rather
        # than treating an omitted closing date as a calibration defect.
        "closingDate": "2026-08-24",
        "sellerDisclosure": "received",
        "hoa": "no",
        "marketContext": scenario["market_context"],
        "listingStatus": scenario["listing_posture"],
        "listingNotes": scenario["market_context"],
        "city": "",
        "county": "",
    }
    if scenario["id"] == "AI-CAL-01":
        offer.update({"daysOnMarket": "2", "listingNotes": "New listing; multiple offers; highest and best deadline."})
    elif scenario["id"] == "AI-CAL-02":
        offer.update({"daysOnMarket": "120", "priceReductionCount": "3", "listingNotes": "Seller motivated; multiple price reductions; few recent showings."})
    return offer


def generate():
    review = _load_review_module()
    catalog = json.loads(FIXTURES.read_text(encoding="utf-8"))
    scenarios = {}
    for scenario in catalog["scenarios"]:
        output = review._rules_fallback(_offer_for_fixture(scenario), {})
        review_flags = []
        market_mode = str(output.get("marketMode") or "")
        summary = str(output.get("summary") or "")
        score = int(output.get("score") or 0)
        if "seller advantage" in market_mode and score < 70:
            review_flags.append("seller_advantage_score_low")
        if "buyer advantage" in market_mode and score >= 85:
            review_flags.append("buyer_advantage_score_high")
        if "seller-favorable" in summary and "buyer advantage" in market_mode:
            review_flags.append("summary_market_mode_conflict")
        scenarios[scenario["id"]] = {
            "id": scenario["id"],
            "review_question": scenario["review_question"],
            "review_flags": review_flags,
            "technical_baseline": output,
        }
    report = {
        "version": "2026-08-03",
        "purpose": "Anonymized deterministic baseline for independent reviewer comparison.",
        "calibration_evidence": False,
        "release_gate": "Five completed independent expert reviews are still required before scoring or wording changes.",
        "source": "api/ai-offer-review.py::_rules_fallback",
        "scenarios": scenarios,
    }
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = generate()
    print(f"Wrote {len(result['scenarios'])} anonymized calibration baselines to {OUTPUT}")

