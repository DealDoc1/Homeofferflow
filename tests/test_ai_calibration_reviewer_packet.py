import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = (ROOT / "docs" / "AI_OFFER_REVIEW_CALIBRATION_REVIEWER_PACKET.md").read_text(
    encoding="utf-8"
)


class AICalibrationReviewerPacketTests(unittest.TestCase):
    def test_packet_contains_all_five_scenarios_and_independence_gate(self):
        for scenario_id in (
            "AI-CAL-01",
            "AI-CAL-02",
            "AI-CAL-03",
            "AI-CAL-04",
            "AI-CAL-05",
        ):
            self.assertIn(scenario_id, PACKET)
        self.assertIn("independently", PACKET.lower())
        self.assertIn("currently practicing Texas real-estate broker or agent", PACKET)

    def test_packet_requires_anonymized_evidence_and_dispositions(self):
        self.assertIn("anonymized", PACKET.lower())
        self.assertIn("choosing the matching scenario ID", PACKET)
        self.assertIn("Recommended disposition", PACKET)
        self.assertIn("A generated AI review output is not calibration evidence", PACKET)

    def test_packet_keeps_release_gate_before_scoring_changes(self):
        self.assertIn("Before changing scoring or wording", PACKET)
        self.assertIn("Product release authority approval", PACKET)
        self.assertIn("Regression results for the existing golden scenarios", PACKET)


if __name__ == "__main__":
    unittest.main()
