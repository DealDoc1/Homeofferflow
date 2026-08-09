import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SellerFollowupStageCopyTests(unittest.TestCase):
    def test_seller_followup_copy_adapts_to_lead_stage(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("const followUpStage = leadStatus === 'new'", source)
        self.assertIn("schedule a short review of your seller workflow and next step", source)
        self.assertIn("confirm the seller workflow scope, pricing, and licensed-provider requirements", source)
        self.assertIn("followUpStage", source)
        self.assertIn("seller_follow_up_email_started", source)


if __name__ == "__main__":
    unittest.main()
