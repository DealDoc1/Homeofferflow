import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT
    / "docs"
    / "release-evidence"
    / "stripe-lifecycle-branch-attempt-2026-08-08.md"
).read_text(encoding="utf-8")


class StripeLifecycleBranchAttemptEvidenceTests(unittest.TestCase):
    def test_evidence_records_failure_and_cleanup_without_overclaiming(self):
        self.assertIn("MIGRATIONS_FAILED", EVIDENCE)
        self.assertIn("Three\nbranch attempts", EVIDENCE)
        self.assertIn("Current branch inventory: production `main` only", EVIDENCE)
        self.assertIn("no Stripe test webhook was created", EVIDENCE)
        self.assertIn("not evidence that the Stripe", EVIDENCE)
        self.assertIn("webhook guard is unsafe", EVIDENCE)

    def test_evidence_requires_bootstrap_prerequisites_before_retry(self):
        self.assertIn("complete, ordered Supabase migration chain/configuration", EVIDENCE)
        self.assertIn("database URL is proven distinct from production", EVIDENCE)


if __name__ == "__main__":
    unittest.main()
