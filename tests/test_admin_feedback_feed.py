import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("admin_dashboard_feedback", ROOT / "api" / "admin-dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AdminFeedbackFeedTests(unittest.TestCase):
    def test_platform_feedback_query_is_privacy_minimized_and_calibration_counted(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("hof_feedback?select=id,issue_type,message,status,role,created_at", source)
        self.assertIn('"feedbackCount": len(feedback)', source)
        self.assertIn('hof_ai_offer_reviews?select=id,created_at', source)
        self.assertIn('"aiReviewOutputCount": len(ai_review_outputs)', source)
        self.assertIn('"aiCalibrationFeedbackCount"', source)
        self.assertIn('"aiCalibrationTarget"', source)
        self.assertIn('"aiCalibrationReady"', source)
        self.assertNotIn("select=*", source[source.index("hof_feedback?"):source.index("hof_feedback?") + 180])


if __name__ == "__main__":
    unittest.main()
