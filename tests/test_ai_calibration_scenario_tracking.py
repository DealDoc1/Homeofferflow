from pathlib import Path
import importlib.util
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_ai_calibration_scenario_tracking.sql").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")


def load_feedback_module():
    path = ROOT / "api" / "submit-feedback" / "index.py"
    spec = importlib.util.spec_from_file_location("submit_feedback_scenario_tracking", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_feedback_module()


class AiCalibrationScenarioTrackingTests(unittest.TestCase):
    def test_database_column_and_index_exist(self):
        self.assertIn("add column if not exists calibration_scenario text", SQL)
        self.assertIn("hof_feedback_ai_calibration_scenario_idx", SQL)

    def test_api_requires_one_of_the_five_documented_cases(self):
        self.assertEqual(len(MODULE.AI_CALIBRATION_SCENARIOS), 5)
        payload = {
            "issueType": "ai_review",
            "message": "Anonymous review",
            "role": "broker",
            "anonymized": True,
        }
        with self.assertRaisesRegex(ValueError, "five documented"):
            MODULE._parse_payload(json.dumps(payload).encode())
        payload["calibrationScenario"] = "AI-CAL-03"
        parsed = MODULE._parse_payload(json.dumps(payload).encode())
        self.assertEqual(parsed["calibration_scenario"], "AI-CAL-03")

    def test_ui_and_admin_require_complete_distinct_scenario_set(self):
        for scenario in ("AI-CAL-01", "AI-CAL-02", "AI-CAL-03", "AI-CAL-04", "AI-CAL-05"):
            self.assertIn(scenario, INDEX)
        self.assertIn("calibrationScenario", INDEX)
        self.assertIn("aiCalibrationScenarioIds", ADMIN)
        self.assertIn("aiCalibrationMissingScenarioIds", ADMIN)
        self.assertIn("set(metrics[\"aiCalibrationScenarioIds\"]) == AI_CALIBRATION_SCENARIOS", ADMIN)


if __name__ == "__main__":
    unittest.main()
