import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")


class GoldenRenderWorkflowTests(unittest.TestCase):
    def test_ci_runs_approved_render_regression_after_unit_tests(self):
        self.assertIn("Check approved golden packet rendering", WORKFLOW)
        self.assertIn("python scripts/check_golden_packet_rendering.py", WORKFLOW)
        self.assertLess(
            WORKFLOW.index("Run unit tests"),
            WORKFLOW.index("Check approved golden packet rendering"),
        )


if __name__ == "__main__":
    unittest.main()
