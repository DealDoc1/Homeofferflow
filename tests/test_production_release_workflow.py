from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "production-release.yml"


class ProductionReleaseWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_release_is_manual_and_confirmation_gated(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirmation:", self.text)
        self.assertIn("inputs.confirmation == 'DEPLOY'", self.text)
        self.assertIn("inputs.confirmation != 'DEPLOY'", self.text)
        self.assertNotIn("on:\n  push:", self.text)

    def test_release_runs_preflight_before_deploying(self):
        self.assertIn("needs: verify", self.text)
        self.assertIn("python scripts/release_preflight.py", self.text)
        self.assertIn("python -m unittest discover -s tests -q", self.text)
        self.assertIn("vercel pull --yes --environment=production", self.text)
        self.assertIn("vercel build --prod", self.text)
        self.assertIn("vercel deploy --prebuilt --prod --yes", self.text)

    def test_release_uses_secret_and_checks_canonical_site(self):
        self.assertIn("secrets.VERCEL_TOKEN", self.text)
        self.assertNotIn("VERCEL_TOKEN=", self.text)
        self.assertIn("vercel inspect", self.text)
        self.assertIn("https://www.homeofferflow.com/", self.text)


if __name__ == "__main__":
    unittest.main()
