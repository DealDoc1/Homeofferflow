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


if __name__ == "__main__":
    unittest.main()
