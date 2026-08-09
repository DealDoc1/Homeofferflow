import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (ROOT / "docs" / "release-evidence" / "stripe-lifecycle-qa-results-2026-08-08.md").read_text(encoding="utf-8")


class StripeLifecycleQaEvidenceTests(unittest.TestCase):
    def test_evidence_identifies_isolated_branch_and_processed_event_types(self):
        self.assertIn("mtalxbxlutkuqcafjsac", EVIDENCE)
        for event_type in (
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "invoice.payment_failed",
            "invoice.paid",
        ):
            self.assertIn(event_type, EVIDENCE)

    def test_evidence_does_not_overclaim_completion(self):
        self.assertIn("does not claim that the full", EVIDENCE)
        self.assertIn("runbook is complete", EVIDENCE)
        self.assertIn("Open items before declaring the runbook complete", EVIDENCE)
        self.assertIn("intermediate snapshot", EVIDENCE)


if __name__ == "__main__":
    unittest.main()
