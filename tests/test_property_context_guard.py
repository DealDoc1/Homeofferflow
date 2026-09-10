import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "ai-offer-review.py"
SPEC = importlib.util.spec_from_file_location("property_context_guard", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PropertyContextGuardTests(unittest.TestCase):
    def test_broker_mls_configuration_is_not_present(self):
        self.assertFalse(hasattr(MODULE, "ENABLE_BROKER_MLS_CONTEXT"))
        self.assertFalse(hasattr(MODULE, "_broker_mls_property_context"))

    def test_customer_interface_does_not_request_broker_mls_context(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("includeBrokerMlsContext", html)
        self.assertIn("No MLS setup required", html)
        self.assertIn("without asking you to find or connect MLS information", html)


if __name__ == "__main__":
    unittest.main()
