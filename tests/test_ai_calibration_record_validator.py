import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_ai_calibration_records", ROOT / "scripts" / "validate_ai_calibration_records.py"
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(module)


class AiCalibrationRecordValidatorTests(unittest.TestCase):
    def _record(self, scenario_id):
        return {
            "scenario_id": scenario_id,
            "review_date": "2026-08-03",
            "reviewer_role": "broker",
            "displayed_score": 82,
            "displayed_market_mode": "Balanced market",
            "displayed_source_model": "rules fallback",
            "useful_output": "The output identified the entered tradeoffs.",
            "misleading_or_unsafe": "None observed.",
            "insufficient_or_missing": "No property-specific market facts.",
            "disclaimer_clear": True,
            "overclaiming_or_advice": False,
            "recommended_change": "Keep wording.",
            "disposition": "useful",
        }

    def test_complete_anonymized_set_passes(self):
        records = [self._record(scenario_id) for scenario_id in module.EXPECTED_IDS]
        self.assertEqual(module.validate(records), [])

    def test_missing_record_field_and_scenario_fail_closed(self):
        record = self._record("AI-CAL-01")
        del record["recommended_change"]
        errors = module.validate([record])
        self.assertTrue(any("recommended_change" in error for error in errors))
        self.assertTrue(any("missing required scenarios" in error for error in errors))

    def test_identifying_data_fails_closed(self):
        records = [self._record(scenario_id) for scenario_id in module.EXPECTED_IDS]
        records[0]["useful_output"] = "Email reviewer@example.com for the MLS address."
        errors = module.validate(records)
        self.assertTrue(any("identifying transaction data" in error for error in errors))

    def test_malformed_container_fails_closed(self):
        self.assertTrue(any("JSON array" in error for error in module.validate({"review": []})))


if __name__ == "__main__":
    unittest.main()
