from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = (ROOT / "docs" / "TXR_SOURCE_OWNER_HANDOFF.md").read_text(encoding="utf-8")


class TxrSourceOwnerHandoffTests(unittest.TestCase):
    def test_handoff_lists_all_restricted_sources_and_separate_gates(self):
        for form in ("TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508"):
            self.assertIn(form, HANDOFF)
        for phrase in ("brokerage administrator", "individual TXR/NAR", "rendered", "completed-PDF QA", "release-authority approval", "private Storage"):
            self.assertIn(phrase, HANDOFF)

    def test_handoff_does_not_claim_source_upload_activates_forms(self):
        self.assertIn("A source upload does not activate", HANDOFF)
        self.assertIn("do not prove", HANDOFF)
        self.assertIn("must upload the exact file and attest", HANDOFF)


if __name__ == "__main__":
    unittest.main()
