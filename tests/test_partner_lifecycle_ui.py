import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")


class PartnerLifecycleUiTests(unittest.TestCase):
    def test_admin_exposes_existing_activation_fields(self):
        self.assertIn("activated_at,agreement_confirmed_at", ADMIN)

    def test_partner_list_has_operational_lifecycle_labels(self):
        self.assertIn("function partnerPlacementLifecycle", INDEX)
        self.assertIn("Launch period", INDEX)
        self.assertIn("Renewal review window", INDEX)
        self.assertIn("Stripe remains the billing authority", INDEX)
        self.assertIn("Collect creative and review placement setup", INDEX)


if __name__ == "__main__":
    unittest.main()
