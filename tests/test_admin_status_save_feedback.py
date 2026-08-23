from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AdminStatusSaveFeedbackTests(unittest.TestCase):
    def test_partner_lead_status_save_announces_busy_state(self):
        start = HTML.index("async function updatePartnerLeadStatus")
        end = HTML.index("function sellerLeadStatusOptions", start)
        segment = HTML[start:end]
        self.assertIn("button.setAttribute('aria-busy', 'true');", segment)
        self.assertIn("button.setAttribute('aria-busy', 'false');", segment)

    def test_seller_lead_status_save_announces_busy_state(self):
        start = HTML.index("async function updateSellerLeadStatus")
        end = HTML.index("function renderAdminRows", start)
        segment = HTML[start:end]
        self.assertIn("button.setAttribute('aria-busy', 'true');", segment)
        self.assertIn("button.setAttribute('aria-busy', 'false');", segment)


if __name__ == "__main__":
    unittest.main()
