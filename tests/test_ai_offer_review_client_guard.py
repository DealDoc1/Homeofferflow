from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class AiOfferReviewClientGuardTests(unittest.TestCase):
    def test_browser_renderer_uses_fixed_product_disclaimer(self):
        start = INDEX.index("function normalizeAiReviewResult(result)")
        end = INDEX.index("function renderAiCleanList", start)
        block = INDEX[start:end]
        self.assertIn("approvedEducationalDisclaimer", block)
        self.assertIn("disclaimer: approvedEducationalDisclaimer", block)
        self.assertNotIn("disclaimer: result.disclaimer ||", block)

    def test_browser_marks_only_authorized_mls_context_as_verified(self):
        start = INDEX.index("function renderAiOfferReviewResult(r, loading = false)")
        end = INDEX.index("function runLiveAiOfferReview", start)
        block = INDEX[start:end]
        self.assertIn("r.propertyContext.mlsVerified === true", block)
        self.assertIn("r.propertyContext.sourceType === 'broker_authorized_reso_mls'", block)
        self.assertIn("Broker-authorized listing context included.", block)

    def test_confidence_credits_verified_broker_listing_facts(self):
        start = INDEX.index("function getReviewConfidence(payload, result = {})")
        end = INDEX.index("function normalizeAiReviewResult", start)
        block = INDEX[start:end]
        self.assertIn("brokerMls.marketEvidence", block)
        self.assertIn("Broker-authorized listing facts and core offer terms were available.", block)
        self.assertIn("Some broker-authorized listing facts and several core offer terms were available.", block)

    def test_property_interview_does_not_promise_unavailable_public_mls_data(self):
        start = INDEX.index('<div class="wizard-step" id="step2">')
        end = INDEX.index('<div class="wizard-step" id="step3">', start)
        block = INDEX[start:end]
        self.assertIn('approved broker listing connection is available', block)
        self.assertIn('Broker listing context when available', block)
        self.assertNotIn('will use public property context for the AI review', block)

    def test_review_copy_does_not_promise_automatic_public_listing_data(self):
        start = INDEX.index("function getInlineAiOfferAnalysis()")
        end = INDEX.index("function buildAiOfferReviewPayload()", start)
        block = INDEX[start:end]
        self.assertNotIn("public listing context is available automatically", block)
        self.assertIn("Broker-authorized listing facts are included only when available.", block)

        start = INDEX.index("function renderAiOfferReviewResult(r, loading = false)")
        end = INDEX.index("function runLiveAiOfferReview", start)
        block = INDEX[start:end]
        self.assertNotIn("Public listing/search context may be included when available", block)
        self.assertIn("Listing facts are included only through an approved broker connection", block)


if __name__ == "__main__":
    unittest.main()
