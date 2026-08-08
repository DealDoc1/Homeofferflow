import pathlib
import unittest


HTML = (pathlib.Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class SellerLeadUrgencyTests(unittest.TestCase):
    def test_admin_seller_queue_surfaces_age_and_needs_contact_state(self):
        self.assertIn("function sellerLeadAgeLabel", HTML)
        self.assertIn("function sellerLeadUrgency", HTML)
        self.assertIn("Needs contact", HTML)
        self.assertIn("sellerLeadAgeLabel(row)", HTML)
        self.assertIn("sellerLeadUrgency(row)", HTML)


if __name__ == "__main__":
    unittest.main()
