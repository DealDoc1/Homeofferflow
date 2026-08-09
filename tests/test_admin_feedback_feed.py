import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("admin_dashboard_feedback", ROOT / "api" / "admin-dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AdminFeedbackFeedTests(unittest.TestCase):
    def test_calibration_threshold_excludes_consumer_feedback(self):
        self.assertTrue(MODULE._is_ai_calibration_evidence({"issue_type": "ai_review", "role": "broker", "calibration_scenario": "AI-CAL-01"}))
        self.assertTrue(MODULE._is_ai_calibration_evidence({"issue_type": "ai_review", "role": "agent", "calibration_scenario": "AI-CAL-02"}))
        self.assertTrue(MODULE._is_ai_calibration_evidence({"issue_type": "ai_review", "role": "brokerage_admin", "calibration_scenario": "AI-CAL-03"}))
        self.assertFalse(MODULE._is_ai_calibration_evidence({"issue_type": "ai_review", "role": "broker", "calibration_scenario": "unlisted"}))
        self.assertFalse(MODULE._is_ai_calibration_evidence({"issue_type": "ai_review", "role": "broker"}))
        self.assertFalse(MODULE._is_ai_calibration_evidence({"issue_type": "ai_review", "role": "homebuyer"}))
        self.assertFalse(MODULE._is_ai_calibration_evidence({"issue_type": "suggestion", "role": "broker"}))

    def test_platform_feedback_query_is_privacy_minimized_and_calibration_counted(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("hof_feedback?select=id,issue_type,calibration_scenario,message,status,role,created_at", source)
        self.assertIn('hof_offer_events?select=*&order=created_at.desc&limit=2000', source)
        self.assertIn('"feedbackCount": len(feedback)', source)
        self.assertIn('"missingFormRequestCount": missing_form_request_count', source)
        self.assertIn('"missingFormRequestCodeCounts": missing_form_request_code_counts', source)
        self.assertIn('"missingFormRecentCodeCounts": missing_form_recent_code_counts', source)
        self.assertIn('"missingFormTopCodes": list(missing_form_request_code_counts)[:5]', source)
        self.assertIn('"missingFormIntakeBriefCopyCount": missing_form_intake_brief_copy_count', source)
        self.assertIn('missing_form_intake_brief_copied', source)
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Missing Form Demand", frontend)
        self.assertIn("missingFormRequestCount", frontend)
        self.assertIn("missingFormTopCodes", frontend)
        self.assertIn('hof_ai_offer_reviews?select=id,created_at', source)
        self.assertIn('"aiReviewOutputCount": len(ai_review_outputs)', source)
        self.assertIn('"aiCalibrationFeedbackCount"', source)
        self.assertIn('"aiCalibrationTarget"', source)
        self.assertIn('"aiCalibrationReady"', source)
        self.assertIn("_is_ai_calibration_evidence(item)", source)
        self.assertNotIn("select=*", source[source.index("hof_feedback?"):source.index("hof_feedback?") + 180])

    def test_missing_form_code_counts_normalize_without_exposing_notes(self):
        counts = MODULE._missing_form_request_code_counts([
            {"issue_type": "missing_addendum", "message": "Need TXR-1507 and txr 1507."},
            {"issue_type": "missing_addendum", "message": "Request TREC-55-1 and trec 55 1."},
            {"issue_type": "bug", "message": "TXR-1507 should not count here."},
        ])
        self.assertEqual(counts, {"TXR-1507": 2, "TREC-55-1": 2})

    def test_missing_form_demand_counts_are_rendered_without_feedback_text(self):
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("missingFormRequestCodeCounts", frontend)
        self.assertIn("missingFormRecentCodeCounts", frontend)
        self.assertIn("Demand counts:", frontend)
        self.assertIn("copyMissingFormIntakeBrief", frontend)
        self.assertIn("Copy source-intake brief", frontend)


if __name__ == "__main__":
    unittest.main()
