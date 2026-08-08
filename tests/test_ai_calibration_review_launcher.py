import pathlib
import unittest


HTML = (pathlib.Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AiCalibrationReviewLauncherTests(unittest.TestCase):
    def test_admin_dashboard_can_open_each_missing_review_scenario(self):
        self.assertIn("function startAiCalibrationReview", HTML)
        self.assertIn("Review ${id}", HTML)
        self.assertIn("missingCalibrationIds", HTML)
        self.assertIn("type.value = 'ai_review'", HTML)
        self.assertIn("scenario.value = scenarioId", HTML)


if __name__ == "__main__":
    unittest.main()
