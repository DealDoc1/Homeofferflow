import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "admin-dashboard.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


admin = load_module("email_health_admin", MODULE_PATH)


class EmailHealthTests(unittest.TestCase):
    def test_summary_exposes_only_aggregate_metrics(self):
        summary = admin._email_health_summary({
            "start_date": "2026-09-01T00:00:00Z",
            "end_date": "2026-09-08T00:00:00Z",
            "totals": {
                "sent": 18,
                "delivered": 17,
                "bounced": 1,
                "complained": 0,
                "failed": 0,
                "delivery_rate": 0.9444,
                "bounce_rate": 0.0556,
                "complaint_rate": 0,
            },
        })
        self.assertTrue(summary["available"])
        self.assertTrue(summary["needsAttention"])
        self.assertEqual(summary["delivered"], 17)
        self.assertNotIn("recipients", summary)

    def test_clean_summary_does_not_need_attention(self):
        summary = admin._email_health_summary({"totals": {"sent": 2, "delivered": 2}})
        self.assertFalse(summary["needsAttention"])


if __name__ == "__main__":
    unittest.main()
