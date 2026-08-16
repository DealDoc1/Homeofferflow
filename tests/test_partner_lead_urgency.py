from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class PartnerLeadUrgencyTests(unittest.TestCase):
    def test_partner_queue_surfaces_age_attention_and_follow_up_ordering(self):
        self.assertIn("function partnerLeadFollowUpPriority", HTML)
        self.assertIn("function prioritizePartnerLeadFollowUpQueue", HTML)
        self.assertIn("function partnerLeadAttentionLabel", HTML)
        self.assertIn("prioritizePartnerLeadFollowUpQueue(partnerLeads).slice(0, 12)", HTML)
        self.assertIn("Checkout follow-up", HTML)
        self.assertIn("Needs contact", HTML)


if __name__ == "__main__":
    unittest.main()
