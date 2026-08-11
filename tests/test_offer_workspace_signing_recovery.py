from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class OfferWorkspaceSigningRecoveryTests(unittest.TestCase):
    def test_stale_buyer_signing_cards_offer_a_copy_only_follow_up_action(self):
        self.assertIn("const needsBuyerReminder = hasDoc && bucketForOffer(o) === 'signing' && needsAttention(o);", HTML)
        self.assertIn("Copy buyer reminder", HTML)
        self.assertIn("root.copyBuyerSigningReminder = async function(offerId)", HTML)
        self.assertIn("buyer_signing_reminder_copied", HTML)

    def test_reminder_requires_agent_review_before_any_external_communication(self):
        start = HTML.index("root.copyBuyerSigningReminder = async function(offerId)")
        end = HTML.index("root.hofRenderOfferWorkspaceV10", start)
        reminder = HTML[start:end]
        self.assertIn("Review it before sending through your approved communication channel.", reminder)
        self.assertNotIn("fetch('/api/", reminder)
        self.assertNotIn("mailto:", reminder)

    def test_created_signwell_documents_are_immediately_treated_as_signing_work(self):
        start = HTML.index("function bucketForOffer(o)")
        end = HTML.index("function signingLabel(o)", start)
        bucket = HTML[start:end]
        self.assertIn("if (status.includes('created') && hasDoc) return 'signing';", bucket)
        self.assertLess(
            bucket.index("if (status.includes('created') && hasDoc) return 'signing';"),
            bucket.index("if (status.includes('generated') || status.includes('created') || hasDoc) return 'generated';"),
        )


if __name__ == "__main__":
    unittest.main()
