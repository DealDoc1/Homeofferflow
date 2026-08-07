import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT / "docs" / "release-evidence"
    / "policy-surface-live-audit-2026-08-07.md"
).read_text(encoding="utf-8")


class PolicySurfaceLiveAuditEvidenceTests(unittest.TestCase):
    def test_current_public_routes_are_recorded_without_side_effects(self):
        for path in (
            "`/`",
            "`/ondemand`",
            "`/terms.html`",
            "`/privacy.html`",
            "`/disclaimer.html`",
            "`/esign-consent.html`",
        ):
            self.assertIn(path, EVIDENCE)
        self.assertEqual(EVIDENCE.count("| 200 | None |"), 6)
        self.assertIn("no Vercel deployment was triggered", EVIDENCE)
        self.assertIn("does not waive authenticated brokerage/TXR QA", EVIDENCE)


if __name__ == "__main__":
    unittest.main()
