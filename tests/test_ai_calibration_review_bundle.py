import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_ai_calibration_review_bundle.py"


class AICalibrationReviewBundleTests(unittest.TestCase):
    def test_bundle_contains_all_five_scenarios_and_no_evidence_claim(self):
        namespace = {"__file__": str(SCRIPT)}
        exec(compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec"), namespace)
        with tempfile.TemporaryDirectory() as temp:
            output = namespace["build"](Path(temp))
            records = json.loads((output / "review-record-template.json").read_text(encoding="utf-8"))
            self.assertEqual(
                [item["scenario_id"] for item in records["reviews"]],
                ["AI-CAL-01", "AI-CAL-02", "AI-CAL-03", "AI-CAL-04", "AI-CAL-05"],
            )
            self.assertIn("not calibration evidence", (output / "README.md").read_text(encoding="utf-8"))
            self.assertIn("technical-baseline.json", {path.name for path in output.iterdir()})


if __name__ == "__main__":
    unittest.main()
