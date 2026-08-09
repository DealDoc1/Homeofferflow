import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AiCalibrationReviewerEmailTests(unittest.TestCase):
    def test_scenario_specific_email_action_is_privacy_safe_and_tracked(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function emailAiCalibrationReviewer(scenarioId)", source)
        self.assertIn("ai_calibration_reviewer_email_started", source)
        self.assertIn("calibrationScenario: scenario", source)
        self.assertIn("mailto:?subject=", source)
        self.assertIn("Email ${id}", source)


if __name__ == "__main__":
    unittest.main()
