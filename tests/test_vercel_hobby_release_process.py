from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VercelHobbyReleaseProcessTests(unittest.TestCase):
    def test_automatic_git_deployments_are_disabled(self):
        config = json.loads((ROOT / "vercel.json").read_text())
        self.assertEqual(config["git"]["deploymentEnabled"], False)

    def test_release_documentation_requires_one_explicit_production_deploy(self):
        guide = (ROOT / "docs" / "VERCEL_HOBBY_RELEASE_PROCESS.md").read_text()
        self.assertIn("vercel deploy --prod --yes", guide)
        self.assertIn("full local test suite", guide)
        self.assertIn("--expected-deploy-author-email andrewchri@gmail.com", guide)
        self.assertIn("PRODUCTION_RELEASE_CHECKLIST.md", guide)

    def test_authoritative_checklist_keeps_packet_qa_and_production_gates_together(self):
        checklist = (ROOT / "docs" / "PRODUCTION_RELEASE_CHECKLIST.md").read_text()
        self.assertIn("Every applicable blank, checkbox, initial, signature, and date", checklist)
        self.assertIn("release_preflight.py", checklist)
        self.assertIn("vercel deploy --prod --yes --scope dealdoc1s-projects", checklist)
        self.assertIn("never send Stripe test", checklist)
        self.assertIn("production database", checklist)
        self.assertIn("Restricted Texas REALTORS", checklist)
        self.assertIn("exact SHA-256 fingerprint", checklist)
        self.assertIn("Source approval has not been mistaken for workflow activation", checklist)
        self.assertIn("do not invoke an unverified or stale deploy-hook URL", checklist)
        self.assertIn("Scan production runtime errors", checklist)

    def test_manual_release_gate_runs_preflight_without_deploying(self):
        workflow = (ROOT / ".github" / "workflows" / "release-gate.yml").read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("base_ref:", workflow)
        self.assertIn('default: origin/main', workflow)
        self.assertIn("python -m unittest discover -s tests -q", workflow)
        self.assertIn("python scripts/release_preflight.py", workflow)
        self.assertIn("--expected-deploy-author-email", workflow)
        self.assertIn("No Vercel deployment was started", workflow)


if __name__ == "__main__":
    unittest.main()
