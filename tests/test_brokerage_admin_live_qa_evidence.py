import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "BROKERAGE_ADMIN_LIVE_QA_2026-08-03.md").read_text(encoding="utf-8")


class BrokerageAdminLiveQaEvidenceTests(unittest.TestCase):
    def test_record_separates_public_checks_from_authenticated_qa(self):
        self.assertIn("does not claim authenticated UI completion", DOC)
        self.assertIn("Not yet verified", DOC)
        self.assertIn("authenticated active `brokerage_admin` session", DOC)

    def test_record_keeps_restricted_sources_gated(self):
        self.assertIn("No source form was uploaded", DOC)
        self.assertIn("no restricted workflow was activated", DOC)


if __name__ == "__main__":
    unittest.main()
