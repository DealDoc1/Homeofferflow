import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")


class GoldenRenderWorkflowTests(unittest.TestCase):
    def test_ci_runs_approved_render_regression_after_unit_tests(self):
        self.assertIn("Check approved golden packet rendering", WORKFLOW)
        self.assertIn("run: python scripts/check_golden_packet_rendering.py --cross-platform", WORKFLOW)
        self.assertNotIn("python scripts/check_golden_packet_rendering.py --structural-only", WORKFLOW)
        self.assertIn("apt-get install --no-install-recommends -y poppler-utils", WORKFLOW)
        self.assertLess(
            WORKFLOW.index("Run unit tests"),
            WORKFLOW.index("Check approved golden packet rendering"),
        )

    def test_render_guard_bases_its_check_on_exact_signer_geometry(self):
        checker = (ROOT / "scripts" / "check_golden_packet_rendering.py").read_text(encoding="utf-8")
        self.assertIn("SIGNING_GEOMETRY_KEYS", checker)
        self.assertIn("def _field_geometry(fields):", checker)
        self.assertIn('"field_geometry": _field_geometry(fields)', checker)
        self.assertIn('signing field placement changed', checker)
        self.assertIn('"field_geometry": scenario["field_geometry"]', checker)


if __name__ == "__main__":
    unittest.main()
