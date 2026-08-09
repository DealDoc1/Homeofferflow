from pathlib import Path
import unittest


WORKFLOW = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "production-release.yml").read_text(encoding="utf-8")


class ProductionDeployTimeoutTests(unittest.TestCase):
    def test_prebuilt_deploy_has_a_bounded_runtime(self):
        self.assertIn("timeout --foreground 8m vercel deploy --prebuilt --prod", WORKFLOW)
        self.assertIn("diagnosable failure", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
