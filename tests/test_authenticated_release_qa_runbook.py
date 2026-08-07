import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "AUTHENTICATED_RELEASE_QA.md").read_text(encoding="utf-8")


class AuthenticatedReleaseQaRunbookTests(unittest.TestCase):
    def test_runbook_requires_token_and_preserves_no_signing_gate(self):
        self.assertIn("HOF_ACCESS_TOKEN", DOC)
        self.assertIn("signing_sent: false", DOC)
        self.assertIn("Completed-signature QA is a separate gate", DOC)

    def test_runbook_covers_all_supported_forms_and_privacy_contract(self):
        for form in ("TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508"):
            self.assertIn(form, DOC)
        self.assertIn("document contents", DOC)
        self.assertIn("source secrets", DOC)


if __name__ == "__main__":
    unittest.main()
