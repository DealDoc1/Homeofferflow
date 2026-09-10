import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "txr_signwell_geometry_baseline",
    ROOT / "scripts" / "check_txr_signwell_geometry_baseline.py",
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class TxrSignwellGeometryBaselineTests(unittest.TestCase):
    def test_current_released_maps_match_the_approved_baseline(self):
        import json

        expected = json.loads(CHECKER.BASELINE_PATH.read_text(encoding="utf-8"))
        matches, reason = CHECKER.compare(CHECKER.build_baseline(), expected)
        self.assertTrue(matches, reason)

    def test_one_pixel_signature_shift_requires_a_new_review(self):
        baseline = {
            "version": 1,
            "coordinate_system": "SignWell 96-DPI top-origin US Letter",
            "forms": {
                "TXR1507": [{
                    "api_id": "txr1507_client1_signature_p2",
                    "type": "signature",
                    "page": 2,
                    "x": 280,
                    "y": 668,
                    "width": 175,
                    "height": 24,
                    "recipient_id": "client_1",
                    "required": True,
                }],
            },
        }
        shifted = {
            **baseline,
            "forms": {
                "TXR1507": [{**baseline["forms"]["TXR1507"][0], "y": 669}],
            },
        }
        matches, reason = CHECKER.compare(shifted, baseline)
        self.assertFalse(matches)
        self.assertEqual(reason, "TXR1507: txr1507_client1_signature_p2 placement changed")

    def test_ci_runs_the_standalone_geometry_guard(self):
        workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        self.assertIn("Check standalone TXR signer geometry", workflow)
        self.assertIn("python scripts/check_txr_signwell_geometry_baseline.py", workflow)


if __name__ == "__main__":
    unittest.main()
