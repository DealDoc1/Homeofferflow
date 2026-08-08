import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProductionVerifiedSourceSyncTests(unittest.TestCase):
    def test_production_copy_matches_staging_source(self):
        staging = ROOT / "api" / "fill_pdf_20_19_staging.py"
        bundled = ROOT / "lib" / "verified_20_19.py"
        self.assertEqual(
            hashlib.sha256(staging.read_bytes()).hexdigest(),
            hashlib.sha256(bundled.read_bytes()).hexdigest(),
            "lib/verified_20_19.py must be regenerated whenever the verified staging source changes",
        )

    def test_production_adapter_loads_bundled_source_path(self):
        source = (ROOT / "lib" / "production_adapter.py").read_text(encoding="utf-8")
        self.assertIn('parent / "verified_20_19.py"', source)
        self.assertNotIn('parent.parent / "api" / "fill_pdf_20_19_staging.py"', source)


if __name__ == "__main__":
    unittest.main()
