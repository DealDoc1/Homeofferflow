import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT / "docs" / "release-evidence"
    / "ondemand-authentication-preflight-2026-08-07.md"
).read_text(encoding="utf-8")


class OnDemandAuthenticationPreflightEvidenceTests(unittest.TestCase):
    def test_public_launch_and_membership_state_are_explicit(self):
        for marker in (
            "$0 today",
            "$29/month",
            "cancel-anytime",
            "one active `broker_admin` membership",
            "active test-agent membership",
            "Andrew's current brokerage membership is pending",
        ):
            self.assertIn(marker, EVIDENCE)

    def test_evidence_does_not_claim_restricted_form_or_signature_qa(self):
        for marker in (
            "not\nevidence of authenticated dashboard QA",
            "No sign-in email was sent",
            "No sign-in email was sent, no draft agreement was created, no SignWell document",
            "Remaining gate",
        ):
            self.assertIn(marker, EVIDENCE)


if __name__ == "__main__":
    unittest.main()
