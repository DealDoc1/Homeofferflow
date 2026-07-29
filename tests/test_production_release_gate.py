import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_production_release_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("production_release_gate", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release_gate = load_module()


class ProductionReleaseGateTests(unittest.TestCase):
    def test_preflight_targets_published_trec_20_19_route(self):
        self.assertEqual(release_gate.CURRENT_CONTRACT.name, "20-19_0.pdf")
        self.assertTrue(release_gate.CURRENT_CONTRACT.is_file())
        self.assertIn(
            "fill_pdf_20_19_production_adapter",
            release_gate.PRODUCTION_ENTRYPOINT.read_text(encoding="utf-8"),
        )

    def test_preflight_includes_tests_and_rendered_golden_regression(self):
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("unittest", source)
        self.assertIn("check_golden_packet_rendering.py", source)
        self.assertIn("completed-signature", source)

    def test_signwell_debug_output_is_opt_in_and_recipient_safe(self):
        for relative_path in ("api/fill-pdf.py", "api/fill_pdf_20_19_staging.py"):
            source = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn('SIGNWELL_DEBUG = os.environ.get("SIGNWELL_DEBUG", "false")', source)
            self.assertIn("def signwell_debug(event, details):", source)
            self.assertNotIn('"recipient_emails"', source)


if __name__ == "__main__":
    unittest.main()
