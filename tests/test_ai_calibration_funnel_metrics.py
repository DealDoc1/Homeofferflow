import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AiCalibrationFunnelMetricTests(unittest.TestCase):
    def test_reviewer_funnel_events_are_logged_without_review_content(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("ai_calibration_review_started", source)
        self.assertIn("ai_calibration_reviewer_packet_downloaded", source)
        self.assertIn("ai_calibration_review_completed", source)
        self.assertIn("calibrationScenario", source)

    def test_admin_payload_and_card_surface_reviewer_funnel(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"aiCalibrationReviewStartCount"', backend)
        self.assertIn('"aiCalibrationPacketDownloadCount"', backend)
        self.assertIn('"aiCalibrationReviewerInviteCopyCount"', backend)
        self.assertIn('"aiCalibrationReviewCompletionCount"', backend)
        self.assertIn('aiCalibrationReviewCompletionRate', backend)
        self.assertIn('aiCalibrationScenarioFunnel', backend)
        self.assertIn("reviewer starts", frontend)
        self.assertIn("packet downloads", frontend)
        self.assertIn("completed", frontend)
        self.assertIn("copyAiCalibrationReviewerInvite", frontend)
        self.assertIn("reviewer outreach templates copied", frontend)
        self.assertIn("Scenario funnel", frontend)


if __name__ == "__main__":
    unittest.main()
