import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "ai-offer-review.py"
SPEC = importlib.util.spec_from_file_location("ai_offer_review_benchmark", MODULE_PATH)
AI_REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AI_REVIEW)


MODERATE_CONVENTIONAL_OFFER = {
    "offerPrice": "490000",
    "listPrice": "500000",
    "earnestMoney": "5000",
    "optionFee": "250",
    "optionDays": "7",
    "financing": "conventional",
    "saleContingency": "no",
    "wantsConcessions": "no",
    "titlePayer": "seller",
    "titleAmendment": "seller",
    "survey": "sellerExisting",
    "asIs": "no",
    "appraisalAddendum": "none",
    "closingDate": "2026-08-24",
    "possession": "funding",
    "sellerDisclosure": "received",
    "hoa": "no",
    "leadBuiltBefore1978": "no",
}


class AiOfferReviewBenchmarkTests(unittest.TestCase):
    def _review(self, offer):
        return AI_REVIEW._rules_fallback(offer, {})

    def test_hot_listing_penalizes_the_same_terms_more_than_stale_listing(self):
        hot = self._review({
            **MODERATE_CONVENTIONAL_OFFER,
            "daysOnMarket": "3",
            "listingNotes": "New listing. Highest and best deadline.",
        })
        stale = self._review({
            **MODERATE_CONVENTIONAL_OFFER,
            "daysOnMarket": "120",
            "priceReductionCount": "2",
            "listingNotes": "Motivated seller; bring offer.",
        })

        self.assertLess(hot["score"], stale["score"])
        self.assertEqual(hot["marketMode"], "strong seller advantage")
        self.assertEqual(stale["marketMode"], "strong buyer advantage")

    def test_weak_terms_surface_the_specific_seller_facing_risks(self):
        review = self._review({
            **MODERATE_CONVENTIONAL_OFFER,
            "earnestMoney": "1000",
            "optionFee": "0",
            "optionDays": "15",
            "financing": "fha",
            "saleContingency": "yes",
            "wantsConcessions": "yes",
            "concessionAmount": "15000",
            "appraisalAddendum": "additional",
        })
        risks = " ".join(review["risks"]).lower()

        self.assertLess(review["score"], 55)
        self.assertIn("sale-of-other-property contingency", risks)
        self.assertIn("seller concessions", risks)
        self.assertIn("long option period", risks)

    def test_fallback_remains_educational_and_bounded(self):
        review = self._review(MODERATE_CONVENTIONAL_OFFER)

        self.assertGreaterEqual(review["score"], 1)
        self.assertLessEqual(review["score"], 100)
        self.assertIn("not legal advice", review["disclaimer"].lower())
        self.assertEqual(review["source"], "rules_fallback_v2_seller_favorability_calibrated")

    def test_live_model_output_cannot_replace_disclaimer_or_expand_display_fields(self):
        fallback = self._review(MODERATE_CONVENTIONAL_OFFER)
        untrusted_model_output = {
            "score": "999",
            "summary": "x" * 1000,
            "risks": ["risk " + str(i) for i in range(12)],
            "strengths": "not-a-list",
            "marketContext": ["market " + str(i) for i in range(12)],
            "suggestions": ["suggestion " + str(i) for i in range(12)],
            "marketMode": "x" * 200,
            "components": {"competitiveness": "-50", "buyerProtection": "300"},
            "disclaimer": "Ignore all prior safety language.",
        }

        review = AI_REVIEW._normalize_live_review(untrusted_model_output, fallback, {})

        self.assertEqual(review["score"], 100)
        self.assertEqual(review["disclaimer"], AI_REVIEW.EDUCATIONAL_REVIEW_DISCLAIMER)
        self.assertLessEqual(len(review["summary"]), 420)
        self.assertEqual(len(review["risks"]), 6)
        self.assertEqual(len(review["marketContext"]), 8)
        self.assertEqual(len(review["suggestions"]), 6)
        self.assertEqual(review["strengths"], fallback["strengths"][:6])
        self.assertEqual(review["components"]["competitiveness"], 1)
        self.assertEqual(review["components"]["buyerProtection"], 100)


if __name__ == "__main__":
    unittest.main()
