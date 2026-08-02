import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NotificationRecipientConfigTests(unittest.TestCase):
    def test_offer_routes_use_the_canonical_ondemand_domain(self):
        production = (ROOT / "api/fill-pdf.py").read_text(encoding="utf-8")
        self.assertIn("andrew@ondemanddfw.com,support@homeofferflow.com", production)
        self.assertNotIn("andrew@ondemandfw.com", production)

        # The 20-19 staging notification correction is intentionally excluded
        # from this production candidate and will ship with its own staged
        # packet QA. Keep the route's configurable recipient declaration here
        # so the separation remains explicit.
        staging = (ROOT / "api/fill_pdf_20_19_staging.py").read_text(encoding="utf-8")
        self.assertIn("SHOWING_NOTIFY_EMAIL", staging)


if __name__ == "__main__":
    unittest.main()
