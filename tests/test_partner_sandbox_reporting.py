import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADMIN_PATH = ROOT / "api" / "admin-dashboard.py"


def load_admin_module():
    spec = importlib.util.spec_from_file_location("partner_sandbox_reporting_admin", ADMIN_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADMIN = load_admin_module()


class PartnerSandboxReportingTests(unittest.TestCase):
    def test_known_sandbox_sources_are_excluded(self):
        self.assertTrue(ADMIN._is_sandbox_partner_lead({"source": "sandbox_checkout_test"}))
        self.assertTrue(ADMIN._is_sandbox_partner_lead({"source": "sandbox_webhook_end_to_end"}))

    def test_test_mode_checkout_identifier_is_excluded(self):
        self.assertTrue(ADMIN._is_sandbox_partner_lead({"stripe_checkout_session_id": "cs_test_example"}))

    def test_live_partner_record_remains_reportable(self):
        self.assertFalse(ADMIN._is_sandbox_partner_lead({
            "source": "founding_partner_landing",
            "stripe_checkout_session_id": "cs_live_example",
        }))


if __name__ == "__main__":
    unittest.main()
