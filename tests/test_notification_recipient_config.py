import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NotificationRecipientConfigTests(unittest.TestCase):
    def test_offer_routes_use_the_canonical_ondemand_domain(self):
        production = (ROOT / "api/fill-pdf.py").read_text(encoding="utf-8")
        self.assertIn("andrew@ondemanddfw.com,support@homeofferflow.com", production)
        self.assertNotIn("andrew@ondemandfw.com", production)

        # Staging must use the same canonical recipient default. This is a
        # notification-only correction and does not change PDF coordinates or
        # the production offer-generation route.
        staging = (ROOT / "api/fill_pdf_20_19_staging.py").read_text(encoding="utf-8")
        self.assertIn("andrew@ondemanddfw.com,support@homeofferflow.com", staging)
        self.assertNotIn("andrew@ondemandfw.com", staging)


if __name__ == "__main__":
    unittest.main()
