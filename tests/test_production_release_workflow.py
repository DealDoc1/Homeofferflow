from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "production-release.yml"


class ProductionReleaseWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_release_requires_manual_or_explicit_marker_confirmation(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirmation:", self.text)
        self.assertIn("inputs.confirmation == 'DEPLOY'", self.text)
        self.assertIn("inputs.confirmation != 'DEPLOY'", self.text)
        self.assertIn("push:", self.text)
        self.assertIn("[deploy-production]", self.text)
        self.assertIn("github.event_name == 'push'", self.text)

    def test_release_runs_preflight_before_deploying(self):
        self.assertIn("needs: verify", self.text)
        self.assertIn("python scripts/release_preflight.py", self.text)
        self.assertIn("python scripts/release_base_ref.py", self.text)
        self.assertIn('base_ref="${{ inputs.base_ref }}"', self.text)
        self.assertNotIn("inputs.base_ref || 'HEAD^'", self.text)
        self.assertIn("python -m unittest discover -s tests -q", self.text)
        self.assertIn("vercel pull --yes --environment=production", self.text)
        self.assertIn("Check Vercel Hobby deployment capacity", self.text)
        self.assertIn("python scripts/check_vercel_deployment_capacity.py", self.text)
        self.assertIn("vercel build --prod", self.text)
        self.assertIn("vercel deploy --prebuilt --prod --yes", self.text)

    def test_release_uses_secret_and_checks_canonical_site(self):
        self.assertIn("secrets.VERCEL_TOKEN", self.text)
        self.assertNotIn("VERCEL_TOKEN=", self.text)
        self.assertIn("vercel inspect", self.text)
        self.assertIn("https://www.homeofferflow.com/", self.text)
        self.assertIn("python scripts/check_production_pwa.py --origin https://www.homeofferflow.com", self.text)


if __name__ == "__main__":
    unittest.main()
