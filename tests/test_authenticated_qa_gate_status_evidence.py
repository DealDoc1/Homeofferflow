import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT / "docs" / "release-evidence"
    / "authenticated-qa-gate-status-2026-08-07.md"
).read_text(encoding="utf-8")


class AuthenticatedQaGateStatusEvidenceTests(unittest.TestCase):
    def test_live_counts_keep_release_gates_open(self):
        for marker in (
            "| `hof_qa_runs` | 16 |",
            "| `hof_qa_results` | 0 |",
            "| `hof_feedback` with `issue_type = 'ai_review'` | 0 |",
            "authenticated brokerage-admin",
            "AI-CAL-01",
            "No production data or signing workflow was changed",
        ):
            self.assertIn(marker, EVIDENCE)


if __name__ == "__main__":
    unittest.main()
