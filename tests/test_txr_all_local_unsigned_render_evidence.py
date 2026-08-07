import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "release-evidence" / "txr-all-local-unsigned-render-review-2026-08-07.md").read_text(
    encoding="utf-8"
)


class TxrAllLocalUnsignedRenderEvidenceTests(unittest.TestCase):
    def test_records_all_four_forms_and_keeps_signing_gate_open(self):
        for form_code in ("TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508"):
            self.assertIn(form_code, DOC)
        self.assertIn("15 rendered pages", DOC)
        self.assertIn("controlled completed-signature", DOC)
        self.assertIn("remain disabled", DOC)


if __name__ == "__main__":
    unittest.main()
