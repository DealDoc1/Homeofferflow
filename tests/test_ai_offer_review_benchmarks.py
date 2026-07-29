import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "ai-offer-review.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ai_offer_review_benchmarks", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ai_review = load_module()


class AiOfferReviewBenchmarkTests(unittest.TestCase):
    """Deterministic calibration guardrails for the no-cost review engine.

    These do not claim to be a pricing recommendation or substitute for a
    broker's market analysis. They only protect the intended directional
    behavior of the educational seller-favorability score while live market
    context and Gemini output are unavailable or being calibrated.
    """

    def test_clean_cash_offer_is_seller_favorable_without_market_context(self):
        review = ai_review._rules_fallback(
            {
                "offerPrice": "510000",
                "listPrice": "500000",
                "earnestMoney": "15000",
                "optionFee": "1000",
                "optionDays": "3",
                "financing": "cash",
                "saleContingency": "no",
                "wantsConcessions": "no",
                "titlePayer": "buyer",
                "titleAmendment": "buyer",
                "survey": "buyerNew",
                "asIs": "yes",
                "appraisalAddendum": "none",
                "closingDate": "2026-08-15",
                "possession": "funding",
                "sellerDisclosure": "received",
                "hoa": "no",
            }
        )

        self.assertGreaterEqual(review["score"], 78)
        self.assertEqual(review["source"], "rules_fallback_v2_seller_favorability_calibrated")
        self.assertTrue(any("Cash financing" in item for item in review["strengths"]))
        self.assertTrue(any("No sale-of-other-property" in item for item in review["strengths"]))
        self.assertIn("not legal advice", review["disclaimer"].lower())

    def test_contingent_low_offer_is_materially_weaker_than_clean_cash_offer(self):
        clean = ai_review._rules_fallback(
            {
                "offerPrice": "510000",
                "listPrice": "500000",
                "earnestMoney": "15000",
                "optionFee": "1000",
                "optionDays": "3",
                "financing": "cash",
                "saleContingency": "no",
                "wantsConcessions": "no",
                "titlePayer": "buyer",
                "asIs": "yes",
                "appraisalAddendum": "none",
                "closingDate": "2026-08-15",
                "possession": "funding",
            }
        )
        weak = ai_review._rules_fallback(
            {
                "offerPrice": "470000",
                "listPrice": "500000",
                "earnestMoney": "1500",
                "optionFee": "100",
                "optionDays": "14",
                "financing": "fha",
                "saleContingency": "yes",
                "wantsConcessions": "yes",
                "concessionAmount": "12000",
                "titlePayer": "seller",
                "survey": "sellerExisting",
                "appraisalAddendum": "additional",
                "closingDate": "2026-10-15",
                "hoa": "unknown",
            }
        )

        self.assertLessEqual(weak["score"], 50)
        self.assertGreaterEqual(clean["score"] - weak["score"], 25)
        combined_risks = " ".join(weak["risks"]).lower()
        self.assertIn("sale-of-other-property contingency", combined_risks)
        self.assertIn("seller concessions", combined_risks)

    def test_market_context_materially_changes_an_identical_moderate_offer(self):
        moderate_offer = {
            "offerPrice": "495000",
            "listPrice": "500000",
            "earnestMoney": "5000",
            "optionFee": "250",
            "optionDays": "7",
            "financing": "conventional",
            "saleContingency": "no",
            "wantsConcessions": "no",
            "titlePayer": "seller",
            "survey": "sellerExisting",
            "appraisalAddendum": "none",
            "closingDate": "2026-09-01",
            "possession": "funding",
            "sellerDisclosure": "received",
            "hoa": "no",
        }
        hot = ai_review._rules_fallback(
            moderate_offer,
            {
                "found": True,
                "daysOnMarket": "3",
                "status": "active",
                "propertySummary": "New listing with multiple offers.",
            },
        )
        stale = ai_review._rules_fallback(
            moderate_offer,
            {
                "found": True,
                "daysOnMarket": "95",
                "status": "active",
                "priceChanges": "Reduced twice.",
                "propertySummary": "Seller motivated.",
            },
        )

        self.assertEqual(hot["marketMode"], "strong seller advantage")
        self.assertEqual(stale["marketMode"], "strong buyer advantage")
        self.assertGreaterEqual(stale["score"] - hot["score"], 25)
        self.assertLess(hot["components"]["marketFit"], stale["components"]["marketFit"])

    def test_components_are_bounded_and_complete(self):
        review = ai_review._rules_fallback({"financing": "cash", "saleContingency": "no"})
        self.assertEqual(
            set(review["components"]),
            {"contractQuality", "competitiveness", "closingCertainty", "buyerProtection", "marketFit"},
        )
        for score in review["components"].values():
            self.assertGreaterEqual(score, 1)
            self.assertLessEqual(score, 100)


if __name__ == "__main__":
    unittest.main()
