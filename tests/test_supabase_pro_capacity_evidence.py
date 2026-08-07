import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT / "docs" / "release-evidence"
    / "supabase-pro-capacity-and-advisor-review-2026-08-07.md"
).read_text(encoding="utf-8")


class SupabaseProCapacityEvidenceTests(unittest.TestCase):
    def test_evidence_records_live_plan_and_preserves_release_gates(self):
        for marker in (
            "Plan: `pro`",
            "Status: `ACTIVE_HEALTHY`",
            "427 tests",
            "hof_standalone_agreements` form-code constraint accepts exactly",
            "Do not apply a blanket `revoke all ... from authenticated` migration.",
            "Completed-signature visual QA",
            "One intentional bundled production deployment",
        ):
            self.assertIn(marker, EVIDENCE)

    def test_evidence_does_not_claim_legal_form_release(self):
        self.assertIn("does not mark the roadmap complete", EVIDENCE)
        self.assertIn("Authenticated point-of-use QA", EVIDENCE)


if __name__ == "__main__":
    unittest.main()
