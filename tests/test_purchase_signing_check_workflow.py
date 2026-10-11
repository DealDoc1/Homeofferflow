from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PurchaseSigningCheckWorkflowTests(unittest.TestCase):
    def test_workflow_uses_reviewed_main_existing_target_and_no_deployment(self):
        text = (ROOT / ".github/workflows/purchase-signing-qa.yml").read_text()
        self.assertIn("github.ref == 'refs/heads/main'", text)
        self.assertIn("inputs.confirmation == 'QA_ONLY'", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("environment: production", text)
        self.assertIn("prj_LupoeEEcWigvtw6CII2bL46l0RB3", text)
        self.assertIn("team_BZUBDsoLMwlnaXtIES35YT4S", text)
        for forbidden in ("vercel build", "vercel deploy", "vercel env add", "--token=", "write-all"):
            self.assertNotIn(forbidden, text)
        self.assertIn("vercel@57.0.0", text)

    def test_duplicate_attempt_is_reserved_before_send_and_only_safe_artifacts_are_exported(self):
        text = (ROOT / ".github/workflows/purchase-signing-qa.yml").read_text()
        self.assertLess(text.index("Refuse a duplicate controlled test attempt"),
                        text.index("Record the attempt before the provider call"))
        self.assertLess(text.index("Record the attempt before the provider call"),
                        text.index("Send exactly one nonbinding parallel test"))
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn("retention-days: 90", text)
        self.assertIn("--expected-layout-sha256", text)
        self.assertNotIn("path: .vercel", text)
        self.assertNotIn("path: tmp/", text.replace("path: tmp/controlled-purchase-qa/manifest.json", "")
                         .replace("path: tmp/controlled-purchase-qa/receipt.json", ""))


if __name__ == "__main__":
    unittest.main()
