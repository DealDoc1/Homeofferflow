from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class AdminSellerFollowUpTests(unittest.TestCase):
    def test_seller_follow_up_uses_package_context_without_exposing_new_data(self):
        self.assertIn("sellerLeadFollowUpAction", INDEX)
        self.assertIn("HomeOfferFlow seller follow-up", INDEX)
        self.assertIn("Package interest: ${packageName}.", INDEX)
        self.assertIn("Partner interests: ${partners}.", INDEX)
        self.assertIn('>Follow up</a>', INDEX)


if __name__ == "__main__":
    unittest.main()
