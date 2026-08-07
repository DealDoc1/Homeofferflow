from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = (ROOT / "docs" / "TXR_1507_AUTHENTICATED_QA.md").read_text(encoding="utf-8")


class Txr1507AuthenticatedQaRunbookTests(unittest.TestCase):
    def test_runbook_keeps_signing_gated(self):
        for phrase in (
            "individual agent authorization attestation",
            "completed signed-PDF visual review",
            "HomeOfferFlow release-authority approval",
            "never\nsends a SignWell document",
        ):
            self.assertIn(phrase, RUNBOOK)

    def test_runbook_uses_both_signer_layouts(self):
        self.assertIn("--clients 1", RUNBOOK)
        self.assertIn("--clients 2", RUNBOOK)
        self.assertIn("one-client and two-client signer layouts", RUNBOOK)


if __name__ == "__main__":
    unittest.main()

