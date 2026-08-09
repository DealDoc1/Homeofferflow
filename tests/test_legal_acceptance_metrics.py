import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LegalAcceptanceMetricTests(unittest.TestCase):
    def test_acceptance_event_is_once_per_policy_session(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("legal_terms_accepted", source)
        self.assertIn("hof_legal_acceptance_", source)
        self.assertIn("policyVersion: LEGAL_POLICY_VERSION", source)

    def test_admin_payload_and_card_surface_acceptance_count(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"legalAcceptanceCount"', backend)
        self.assertIn("Legal Acceptance Events", frontend)
        self.assertIn("legalAcceptanceCount", frontend)


if __name__ == "__main__":
    unittest.main()
