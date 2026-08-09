import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PartnerActivationFollowupCopyTests(unittest.TestCase):
    def test_paid_partner_followup_is_stage_aware(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("const activationStage = paid && onboarding === 'not_started'", source)
        self.assertIn("complete the partner onboarding details and confirm the launch window", source)
        self.assertIn("finish the remaining onboarding details so the placement can go live", source)
        self.assertIn("partner activation:", source)
        self.assertIn("activationStage", source)


if __name__ == "__main__":
    unittest.main()
