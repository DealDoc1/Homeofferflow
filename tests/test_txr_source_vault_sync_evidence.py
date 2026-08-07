import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "release-evidence" / "txr-source-vault-sync-2026-08-07.md").read_text(
    encoding="utf-8"
)


class TxrSourceVaultSyncEvidenceTests(unittest.TestCase):
    def test_records_all_approved_sources_and_keeps_release_gate_open(self):
        for form_code in ("TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508"):
            self.assertIn(form_code, DOC)
        self.assertIn("SHA-256 match", DOC)
        self.assertIn("controlled completed-signature visual QA", DOC)
        self.assertIn("remain preview-only", DOC)


if __name__ == "__main__":
    unittest.main()
